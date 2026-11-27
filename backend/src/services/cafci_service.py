from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from io import BytesIO
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
# Register the target of Activo.inversores_favoritos for SQLAlchemy.
from src.db.models.inversor_model import Inversor

logger = logging.getLogger(__name__)

CAFCI_URL = "https://api.pub.cafci.org.ar/pb_get"
CAFCI_TIMEOUT_SECONDS = 30


class CafciProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class FciHistoricalPoint:
    quote_date: date
    price: Decimal


@dataclass(frozen=True)
class FciReferenceValue:
    quote_date: date
    value: Decimal


@dataclass(frozen=True)
class FciQuote:
    ticker: str
    name: str
    currency: str
    price: Decimal
    change: Decimal
    quote_date: date
    previous_price: Decimal | None = None
    previous_quote_date: date | None = None
    historical_points: tuple[FciHistoricalPoint, ...] = ()
    legacy_reference_values: tuple[FciReferenceValue, ...] = ()


def _parse_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for date_format in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), date_format).date()
            except ValueError:
                continue
    raise ValueError(f"fecha inválida: {value!r}")


def _parse_number(value: object) -> Decimal:
    number = Decimal(str(value).strip().replace(",", "."))
    if not number.is_finite():
        raise InvalidOperation
    return number


def parse_cafci_workbook(content: bytes) -> list[FciQuote]:
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError) as exc:
        raise CafciProviderError("CAFCI no devolvió una planilla XLSX válida") from exc

    quotes: dict[str, FciQuote] = {}
    skipped_identity = 0
    skipped_quote = 0
    skipped_previous_quote = 0
    skipped_reference_value = 0
    try:
        worksheet = workbook.active
        if worksheet is None:
            raise CafciProviderError("La planilla CAFCI no contiene una hoja activa")
        try:
            previous_quote_date = _parse_date(worksheet.cell(row=9, column=7).value)
        except (ValueError, TypeError):
            previous_quote_date = None
        reference_dates: dict[int, date] = {}
        for column in (10, 11, 12):
            raw_date = worksheet.cell(row=9, column=column).value
            if raw_date is None:
                continue
            try:
                reference_dates[column] = _parse_date(raw_date)
            except (ValueError, TypeError) as exc:
                raise CafciProviderError(
                    f"CAFCI devolvió una fecha de referencia inválida en la columna {column}"
                ) from exc

        for row in worksheet.iter_rows(min_row=10, values_only=True):
            if len(row) <= 20 or row[20] is None:
                continue
            try:
                code_decimal = _parse_number(row[20])
                if code_decimal != code_decimal.to_integral_value():
                    raise ValueError("el código CAFCI no es entero")
                code = int(code_decimal)
            except (InvalidOperation, ValueError, TypeError):
                skipped_identity += 1
                continue

            name = str(row[0] or "").strip()
            currency = str(row[1] or "").strip().upper()
            if not name or currency not in ("ARS", "USD"):
                skipped_identity += 1
                continue
            try:
                quote_date = _parse_date(row[4])
                price = _parse_number(row[5])
                change = _parse_number(row[7]) if row[7] is not None else Decimal("0")
            except (InvalidOperation, ValueError, TypeError):
                skipped_quote += 1
                continue
            if price <= 0:
                skipped_quote += 1
                continue
            previous_price = None
            if previous_quote_date is not None and previous_quote_date < quote_date and row[6] is not None:
                try:
                    candidate_previous_price = _parse_number(row[6])
                    if candidate_previous_price > 0:
                        previous_price = candidate_previous_price.quantize(Decimal("0.000001"))
                except (InvalidOperation, ValueError, TypeError):
                    skipped_previous_quote += 1
            historical_prices: dict[date, Decimal] = {}
            legacy_reference_values: dict[date, Decimal] = {}
            if previous_price is not None and previous_quote_date is not None:
                historical_prices[previous_quote_date] = previous_price
            for column, reference_date in reference_dates.items():
                raw_value = row[column - 1]
                if raw_value is None or reference_date >= quote_date:
                    continue
                try:
                    reference_value = _parse_number(raw_value)
                except (InvalidOperation, ValueError, TypeError):
                    skipped_reference_value += 1
                    continue
                if reference_value > 0:
                    legacy_reference_values[reference_date] = reference_value.quantize(
                        Decimal("0.000001")
                    )
            historical_prices[quote_date] = price.quantize(Decimal("0.000001"))
            ticker = f"FCI-{code}"
            if ticker in quotes:
                raise CafciProviderError(f"El código CAFCI {code} está duplicado")
            quotes[ticker] = FciQuote(
                ticker=ticker,
                name=name[:100],
                currency=currency,
                price=price.quantize(Decimal("0.000001")),
                change=change.quantize(Decimal("0.0001")),
                quote_date=quote_date,
                previous_price=previous_price,
                previous_quote_date=previous_quote_date if previous_price is not None else None,
                historical_points=tuple(
                    FciHistoricalPoint(quote_date=point_date, price=point_price)
                    for point_date, point_price in sorted(historical_prices.items())
                ),
                legacy_reference_values=tuple(
                    FciReferenceValue(quote_date=point_date, value=point_value)
                    for point_date, point_value in sorted(legacy_reference_values.items())
                ),
            )
    finally:
        workbook.close()

    if not quotes:
        raise CafciProviderError("La planilla CAFCI no contiene cuotapartes válidas")
    if skipped_identity or skipped_quote or skipped_previous_quote or skipped_reference_value:
        logger.warning(
            "CAFCI: se omitieron %s filas por identificación, %s por cotización actual, "
            "%s por cotización previa y %s valores de referencia",
            skipped_identity,
            skipped_quote,
            skipped_previous_quote,
            skipped_reference_value,
        )
    return list(quotes.values())


def fetch_cafci_quotes() -> list[FciQuote]:
    request = Request(
        CAFCI_URL,
        headers={"User-Agent": "Invertix/1.0 (CAFCI daily fund quotes)"},
    )
    try:
        with urlopen(request, timeout=CAFCI_TIMEOUT_SECONDS) as response:
            content = response.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise CafciProviderError("No se pudo descargar la planilla diaria de CAFCI") from exc
    return parse_cafci_workbook(content)


def sync_cafci_quotes(db: Session, quotes: list[FciQuote]) -> tuple[int, int]:
    if len({quote.ticker for quote in quotes}) != len(quotes):
        raise CafciProviderError("La lista CAFCI contiene tickers duplicados")

    inserted = 0
    updated = 0
    try:
        assets_by_ticker = {
            asset.ticker: asset
            for asset in db.query(Activo).all()
        }
        for quote in quotes:
            asset = assets_by_ticker.get(quote.ticker)
            if asset is None:
                asset = Activo(
                    ticker=quote.ticker,
                    nombre=quote.name,
                    tipo="fci",
                    moneda=quote.currency,
                    precio_actual=quote.price,
                    fecha_cotizacion=quote.quote_date,
                    variacion_porcentual=quote.change,
                    nivel_riesgo=3,
                    activo=True,
                )
                db.add(asset)
                assets_by_ticker[quote.ticker] = asset
                inserted += 1
            elif asset.fecha_cotizacion is None or quote.quote_date >= asset.fecha_cotizacion:
                asset.nombre = quote.name
                asset.tipo = "fci"
                asset.moneda = quote.currency
                asset.precio_actual = quote.price
                asset.fecha_cotizacion = quote.quote_date
                asset.variacion_porcentual = quote.change
                asset.activo = True
                updated += 1

        db.flush()
        legacy_values_by_date: dict[date, dict[int, Decimal]] = defaultdict(dict)
        quotes_by_date: dict[date, list[tuple[Activo, Decimal]]] = defaultdict(list)
        for quote in quotes:
            asset = assets_by_ticker[quote.ticker]
            for reference_value in quote.legacy_reference_values:
                legacy_values_by_date[reference_value.quote_date][asset.id] = reference_value.value
            history_by_date = {
                point.quote_date: point.price
                for point in quote.historical_points
            }
            if quote.previous_price is not None and quote.previous_quote_date is not None:
                history_by_date.setdefault(quote.previous_quote_date, quote.previous_price)
            history_by_date[quote.quote_date] = quote.price
            for quote_date, price in history_by_date.items():
                quotes_by_date[quote_date].append((asset, price))

        for reference_date, values_by_asset in legacy_values_by_date.items():
            asset_ids = list(values_by_asset)
            for offset in range(0, len(asset_ids), 500):
                batch_ids = asset_ids[offset:offset + 500]
                records = db.query(ActivoCotizacionHistorica).filter(
                    ActivoCotizacionHistorica.activo_id.in_(batch_ids),
                    ActivoCotizacionHistorica.fecha == reference_date,
                ).all()
                for record in records:
                    if Decimal(record.precio) == values_by_asset[record.activo_id]:
                        db.delete(record)

        for quote_date, daily_quotes in quotes_by_date.items():
            assets_for_date = [asset for asset, _ in daily_quotes]
            history_by_key: dict[tuple[int, date], ActivoCotizacionHistorica] = {}
            for offset in range(0, len(assets_for_date), 500):
                asset_ids = [asset.id for asset in assets_for_date[offset:offset + 500]]
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
    return inserted, updated


def sync_cafci_assets() -> tuple[int, int]:
    quotes = fetch_cafci_quotes()
    db = SessionLocal()
    try:
        return sync_cafci_quotes(db, quotes)
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    inserted, updated = sync_cafci_assets()
    print(f"FCI nuevos: {inserted}; actualizados: {updated}")


if __name__ == "__main__":
    main()
