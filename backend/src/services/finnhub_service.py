from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import logging
import time

import finnhub
from sqlalchemy.orm import Session

from src.config.env import settings
from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo
# Register the target of Activo.inversores_favoritos for SQLAlchemy.
from src.db.models.inversor_model import Inversor

logger = logging.getLogger(__name__)
FINNHUB_QUOTE_INTERVAL_SECONDS = 1.1


class FinnhubProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class FinnhubAsset:
    ticker: str
    name: str
    asset_type: str
    currency: str
    price: Decimal
    change: Decimal
    quote_date: date | None


def _positive_decimal(value: object) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def _asset_type(instrument_type: object) -> str | None:
    normalized = str(instrument_type or "").strip().lower()
    if "etf" in normalized or "etp" in normalized or "fund" in normalized:
        return "etf"
    if "adr" in normalized or "depositary" in normalized:
        return "accion"
    if "common stock" in normalized or "equity" in normalized:
        return "accion"
    return None


def _normalize_ticker(symbol: str, exchange: str) -> str:
    ticker = symbol.strip().upper()
    if exchange == "US":
        return ticker if ticker.endswith(".US") else f"{ticker}.US"
    if exchange == "BUE":
        ticker = ticker.split(".")[0]
    return ticker


def fetch_finnhub_assets(
    limit: int | None = None,
    excluded_tickers: set[str] | None = None,
) -> list[FinnhubAsset]:
    max_assets = limit if limit is not None else settings.FINNHUB_MAX_ASSETS
    if max_assets <= 0:
        return []
    excluded = excluded_tickers or set()

    if not settings.FINNHUB_API_KEY:
        raise FinnhubProviderError("FINNHUB_API_KEY no está configurada")
    client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
    try:
        rows = client.stock_symbols("US")
    except Exception as exc:
        raise FinnhubProviderError(
            "No se pudo obtener el listado de símbolos de Finnhub"
        ) from exc
    if not isinstance(rows, list):
        raise FinnhubProviderError(
            "Finnhub devolvió una lista de símbolos inválida"
        )

    assets: dict[str, FinnhubAsset] = {}
    allowed_mics = {"XNAS", "XNYS", "ARCX"}
    quote_errors = 0
    for row in rows:
        if len(assets) >= max_assets:
            break
        if not isinstance(row, dict):
            continue
        symbol = row.get("symbol")
        currency = str(row.get("currency") or "").strip().upper()
        mic = str(row.get("mic") or "").strip().upper()
        instrument_type = row.get("type")
        asset_type = _asset_type(instrument_type)
        if (
            not isinstance(symbol, str)
            or not symbol.strip()
            or currency != "USD"
            or mic not in allowed_mics
            or asset_type is None
        ):
            continue
        ticker = f"{symbol.strip().upper()}.US"
        if (
            len(ticker) > 20
            or ticker in assets
            or ticker in excluded
        ):
            continue
        try:
            payload = client.quote(symbol.strip())
        except Exception as exc:
            quote_errors += 1
            logger.warning(
                "No se pudo consultar Finnhub para %s: %s",
                symbol,
                exc,
            )
            continue
        finally:
            time.sleep(FINNHUB_QUOTE_INTERVAL_SECONDS)
        if not isinstance(payload, dict):
            continue
        price = _positive_decimal(payload.get("c"))
        if price is None:
            continue
        try:
            change = Decimal(str(payload.get("dp") or 0)).quantize(
                Decimal("0.0001")
            )
        except InvalidOperation:
            change = Decimal("0")
        timestamp = payload.get("t")
        quote_date = None
        if isinstance(timestamp, (int, float)) and timestamp > 0:
            quote_date = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            ).date()
        assets[ticker] = FinnhubAsset(
            ticker=ticker,
            name=str(row.get("description") or symbol).strip()[:100],
            asset_type=asset_type,
            currency=currency,
            price=price.quantize(Decimal("0.000001")),
            change=change,
            quote_date=quote_date,
        )
    if quote_errors and not assets:
        raise FinnhubProviderError(
            "Finnhub no permitió consultar cotizaciones; se reintentará más tarde"
        )
    return list(assets.values())


def sync_finnhub_assets(db: Session | None = None) -> tuple[int, int]:
    owns_session = db is None
    if owns_session:
        with SessionLocal() as read_session:
            existing_tickers = {
                ticker
                for (ticker,) in read_session.query(Activo.ticker).all()
            }
    else:
        existing_tickers = {
            ticker
            for (ticker,) in db.query(Activo.ticker).all()
        }

    assets = fetch_finnhub_assets(excluded_tickers=existing_tickers)
    session = db or SessionLocal()
    inserted = 0
    updated = 0
    try:
        for quote in assets:
            asset = session.query(Activo).filter(
                Activo.ticker == quote.ticker
            ).one_or_none()
            if asset is None:
                session.add(Activo(
                    ticker=quote.ticker,
                    nombre=quote.name,
                    tipo=quote.asset_type,
                    moneda=quote.currency,
                    precio_actual=quote.price,
                    fecha_cotizacion=quote.quote_date,
                    variacion_porcentual=quote.change,
                    nivel_riesgo=3 if quote.asset_type in ("accion", "etf") else 4,
                    activo=True,
                ))
                inserted += 1
            else:
                asset.nombre = quote.name
                asset.tipo = quote.asset_type
                asset.moneda = quote.currency
                asset.precio_actual = quote.price
                asset.fecha_cotizacion = quote.quote_date
                asset.variacion_porcentual = quote.change
                asset.activo = True
                updated += 1
        session.commit()
        return inserted, updated
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()
