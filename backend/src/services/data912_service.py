from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import logging
from typing import Literal
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
# Register the target of Activo.inversores_favoritos for SQLAlchemy.
from src.db.models.inversor_model import Inversor

logger = logging.getLogger(__name__)

DATA912_BASE_URL = "https://data912.com"
DATA912_TIMEOUT_SECONDS = 30
DATA912_ENDPOINTS = (
    ("/live/arg_stocks", False),
    ("/live/arg_cedears", False),
    ("/live/arg_notes", False),
    ("/live/arg_corp", False),
    ("/live/arg_bonds", False),
    ("/live/usa_adrs", True),
    ("/live/usa_stocks", True),
)
# Existing databases may still store Disney under its former ticker.
DATA912_CEDEAR_TICKER_ALIASES = {"DIS": "DISN"}


class Data912ProviderError(RuntimeError):
    pass


class Data912HistoryNotFoundError(Data912ProviderError):
    pass


@dataclass(frozen=True)
class Data912Quote:
    ticker: str
    price: Decimal
    change: Decimal
    quote_date: date


@dataclass(frozen=True)
class Data912HistoricalQuote:
    quote_date: date
    price: Decimal
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None


def _positive_decimal(value: object) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def parse_data912_history(
    payload: object,
    ticker: str,
) -> list[Data912HistoricalQuote]:
    if isinstance(payload, dict) and payload.get("Error"):
        raise Data912HistoryNotFoundError(
            f"Data912 no tiene historial para {ticker}: {payload['Error']}"
        )
    if not isinstance(payload, list) or not payload:
        raise Data912HistoryNotFoundError(f"Data912 no devolvió historial para {ticker}")

    quotes = []
    for item in payload:
        if not isinstance(item, dict):
            raise Data912ProviderError(f"Data912 devolvió una fila histórica inválida para {ticker}")
        try:
            quote_date = date.fromisoformat(str(item["date"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise Data912ProviderError(f"Data912 devolvió una fecha inválida para {ticker}") from exc

        price = _positive_decimal(item.get("c"))
        if price is None:
            raise Data912ProviderError(f"Data912 devolvió un cierre inválido para {ticker}")

        open_price = _positive_decimal(item.get("o"))
        high = _positive_decimal(item.get("h"))
        low = _positive_decimal(item.get("l"))
        if not all((open_price, high, low)):
            open_price = high = low = None
        try:
            quotes.append(Data912HistoricalQuote(
                quote_date=quote_date,
                price=price.quantize(Decimal("0.000001")),
                open=open_price.quantize(Decimal("0.000001")) if open_price else None,
                high=high.quantize(Decimal("0.000001")) if high else None,
                low=low.quantize(Decimal("0.000001")) if low else None,
            ))
        except InvalidOperation as exc:
            raise Data912ProviderError(f"Data912 devolvió una cotización fuera de rango para {ticker}") from exc

    return sorted(quotes, key=lambda quote: quote.quote_date)


def parse_data912_bond_history(
    payload: object,
    ticker: str,
) -> list[Data912HistoricalQuote]:
    return parse_data912_history(payload, ticker)


def fetch_data912_history(
    ticker: str,
    market: Literal["bonds", "cedears"],
) -> list[Data912HistoricalQuote]:
    url = f"{DATA912_BASE_URL}/historical/{market}/{quote(ticker, safe='')}"
    request = Request(
        url,
        headers={"User-Agent": "Invertix/1.0 (market history)"},
    )
    try:
        with urlopen(request, timeout=DATA912_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise Data912ProviderError(f"No se pudo consultar el historial de {ticker} en Data912") from exc
    return parse_data912_history(payload, ticker)


def fetch_data912_bond_history(ticker: str) -> list[Data912HistoricalQuote]:
    return fetch_data912_history(ticker, "bonds")


def fetch_data912_cedear_history(ticker: str) -> list[Data912HistoricalQuote]:
    normalized_ticker = ticker.strip().upper()
    market_ticker = DATA912_CEDEAR_TICKER_ALIASES.get(normalized_ticker, normalized_ticker)
    return fetch_data912_history(market_ticker, "cedears")


def parse_data912_quotes(
    payloads: Mapping[str, object],
    quote_date: date | None = None,
) -> list[Data912Quote]:
    quote_date = quote_date or date.today()
    quotes: dict[str, Data912Quote] = {}

    for path, is_us_market in DATA912_ENDPOINTS:
        payload = payloads.get(path)
        if not isinstance(payload, list) or not payload:
            raise Data912ProviderError(f"Data912 devolvió una lista inválida para {path}")

        for item in payload:
            if not isinstance(item, dict):
                raise Data912ProviderError(f"Data912 devolvió un activo inválido para {path}")
            symbol = item.get("symbol")
            if not isinstance(symbol, str) or not symbol.strip():
                raise Data912ProviderError(f"Data912 devolvió un ticker inválido para {path}")

            symbol = symbol.strip().upper()
            ticker = f"{symbol}.US" if is_us_market else symbol
            if len(ticker) > 10:
                raise Data912ProviderError(f"El ticker {ticker} excede VARCHAR(10)")

            price = _positive_decimal(item.get("c"))
            if price is None:
                available_quotes = [
                    quote
                    for quote in (
                        _positive_decimal(item.get("px_bid")),
                        _positive_decimal(item.get("px_ask")),
                    )
                    if quote is not None
                ]
                if not available_quotes:
                    raise Data912ProviderError(f"Data912 no devolvió un precio válido para {ticker}")
                price = available_quotes[0]
                if len(available_quotes) == 2:
                    price = (available_quotes[0] + available_quotes[1]) / Decimal("2")

            try:
                change = Decimal(str(item["pct_change"]))
            except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
                raise Data912ProviderError(
                    f"Data912 devolvió una variación inválida para {ticker}"
                ) from exc
            if not change.is_finite():
                raise Data912ProviderError(f"Data912 devolvió una variación no finita para {ticker}")
            try:
                price = price.quantize(Decimal("0.000001"))
                change = change.quantize(Decimal("0.0001"))
            except InvalidOperation as exc:
                raise Data912ProviderError(
                    f"Data912 devolvió una cotización fuera de rango para {ticker}"
                ) from exc
            if price <= 0 or abs(change) >= Decimal("10000"):
                raise Data912ProviderError(
                    f"Data912 devolvió una cotización fuera de rango para {ticker}"
                )

            if ticker in quotes:
                raise Data912ProviderError(f"Data912 devolvió el ticker duplicado {ticker}")
            quotes[ticker] = Data912Quote(
                ticker=ticker,
                price=price,
                change=change,
                quote_date=quote_date,
            )

    return list(quotes.values())


def fetch_data912_quotes() -> list[Data912Quote]:
    payloads: dict[str, object] = {}
    for path, _ in DATA912_ENDPOINTS:
        request = Request(
            DATA912_BASE_URL + path,
            headers={"User-Agent": "Invertix/1.0 (market price refresh)"},
        )
        try:
            with urlopen(request, timeout=DATA912_TIMEOUT_SECONDS) as response:
                payloads[path] = json.loads(response.read())
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise Data912ProviderError(f"No se pudo consultar Data912 en {path}") from exc
    return parse_data912_quotes(payloads)


def sync_data912_quotes(db: Session, quotes: list[Data912Quote]) -> tuple[int, int]:
    if not quotes:
        raise Data912ProviderError("Data912 no devolvió cotizaciones")
    if len({quote.ticker for quote in quotes}) != len(quotes):
        raise Data912ProviderError("Data912 devolvió tickers duplicados")

    try:
        assets_by_ticker: dict[str, Activo] = {}
        tickers = [quote.ticker for quote in quotes]
        for offset in range(0, len(tickers), 500):
            assets = db.query(Activo).filter(
                Activo.ticker.in_(tickers[offset:offset + 500])
            ).all()
            assets_by_ticker.update({asset.ticker: asset for asset in assets})

        quotes_by_date: dict[date, list[tuple[Activo, Decimal]]] = defaultdict(list)
        updated = 0
        missing = 0
        for quote in quotes:
            asset = assets_by_ticker.get(quote.ticker)
            if asset is None:
                missing += 1
                continue
            asset.precio_actual = quote.price
            asset.variacion_porcentual = quote.change
            asset.fecha_cotizacion = quote.quote_date
            quotes_by_date[quote.quote_date].append((asset, quote.price))
            updated += 1

        for quote_date, daily_quotes in quotes_by_date.items():
            history_by_key: dict[tuple[int, date], ActivoCotizacionHistorica] = {}
            for offset in range(0, len(daily_quotes), 500):
                asset_ids = [
                    asset.id
                    for asset, _ in daily_quotes[offset:offset + 500]
                ]
                records = db.query(ActivoCotizacionHistorica).filter(
                    ActivoCotizacionHistorica.activo_id.in_(asset_ids),
                    ActivoCotizacionHistorica.fecha == quote_date,
                ).all()
                history_by_key.update(
                    {(record.activo_id, record.fecha): record for record in records}
                )

            for asset, price in daily_quotes:
                history_key = (asset.id, quote_date)
                record = history_by_key.get(history_key)
                if record is None:
                    db.add(ActivoCotizacionHistorica(
                        activo_id=asset.id,
                        fecha=quote_date,
                        precio=price,
                    ))
                else:
                    record.precio = price

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return updated, missing


def sync_data912_assets() -> tuple[int, int]:
    quotes = fetch_data912_quotes()
    db = SessionLocal()
    try:
        return sync_data912_quotes(db, quotes)
    finally:
        db.close()
