from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
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
# Register the target of Activo.inversores_favoritos for SQLAlchemy.
from src.db.models.inversor_model import Inversor

logger = logging.getLogger(__name__)

CAFCI_URL = "https://api.pub.cafci.org.ar/pb_get"
CAFCI_TIMEOUT_SECONDS = 30


class CafciProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class FciQuote:
    ticker: str
    name: str
    currency: str
    price: Decimal
    change: Decimal
    quote_date: date


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
    try:
        worksheet = workbook.active
        if worksheet is None:
            raise CafciProviderError("La planilla CAFCI no contiene una hoja activa")
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
            )
    finally:
        workbook.close()

    if not quotes:
        raise CafciProviderError("La planilla CAFCI no contiene cuotapartes válidas")
    if skipped_identity or skipped_quote:
        logger.warning(
            "CAFCI: se omitieron %s filas por datos de identificación y %s por cotizaciones inválidas",
            skipped_identity,
            skipped_quote,
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
    inserted = 0
    updated = 0
    try:
        for quote in quotes:
            asset = db.query(Activo).filter(Activo.ticker == quote.ticker).one_or_none()
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
                inserted += 1
            else:
                asset.nombre = quote.name
                asset.tipo = "fci"
                asset.moneda = quote.currency
                asset.precio_actual = quote.price
                asset.fecha_cotizacion = quote.quote_date
                asset.variacion_porcentual = quote.change
                asset.activo = True
                updated += 1
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
