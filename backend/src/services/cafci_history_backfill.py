from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import argparse
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import json
import logging
import re
import time
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
from src.services.cafci_service import (
    CAFCI_TIMEOUT_SECONDS,
    CafciProviderError,
    FciHistoricalPoint,
    FciQuote,
    fetch_cafci_quotes,
    sync_cafci_quotes,
)

logger = logging.getLogger(__name__)

CAFCI_STATISTICS_URL = "https://estadisticas.cafci.org.ar"
CAFCI_COMPARATOR_PAGE = f"{CAFCI_STATISTICS_URL}/comparador-paso2"
CAFCI_COMPARATOR_CATALOG = f"{CAFCI_STATISTICS_URL}/consulta-de-fondos.json"
CAFCI_COMPARATOR_RESULT = f"{CAFCI_STATISTICS_URL}/comparador-resultado"
COMPARATOR_MAX_FUNDS = 4
COMPARATOR_REQUEST_DELAY_SECONDS = 1.2
COMPARATOR_RETRY_DELAYS_SECONDS = (1, 3)
COMPARATOR_FORBIDDEN_RETRY_DELAYS_SECONDS = (30, 60, 120)
COMPARATOR_COOLDOWN_EVERY_GROUPS = 100
COMPARATOR_COOLDOWN_SECONDS = 30
MAX_HISTORY_DEVIATION_RATIO = Decimal("0.50")
MAX_INTERPOLATION_GAP_DAYS = 14
PRICE_QUANTUM = Decimal("0.000001")
TICKER_CODE_PATTERN = re.compile(r"^FCI-(\d+)$")
PERCENT_PATTERN = re.compile(r"([+-]?[\d.,]+)\s*%")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class FciComparisonPoint:
    quote_date: date
    cumulative_return: Decimal


@dataclass(frozen=True)
class FciBackfillResult:
    assets_found: int
    assets_backfilled: int
    assets_without_comparator_mapping: int
    assets_without_quote: int
    assets_without_usable_series: int
    points_added: int
    points_corrected: int
    suspicious_points_removed: int


class _ComparisonTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell_parts is not None:
            self._row.append(" ".join(" ".join(self._cell_parts).split()))
            self._cell_parts = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def parse_comparator_html(
    content: str,
    class_ids: Sequence[int],
) -> dict[int, tuple[FciComparisonPoint, ...]]:
    parser = _ComparisonTableParser()
    parser.feed(content)
    header_index = next(
        (
            index
            for index, row in enumerate(parser.rows)
            if row and row[0].strip().casefold() == "fecha"
        ),
        None,
    )
    expected_columns = len(class_ids) + 1
    if header_index is None or len(parser.rows[header_index]) != expected_columns:
        raise CafciProviderError("CAFCI devolvió una tabla comparativa con formato inesperado")

    series: dict[int, list[FciComparisonPoint]] = {
        class_id: [] for class_id in class_ids
    }
    for row in parser.rows[header_index + 1:]:
        if not row:
            continue
        try:
            point_date = date.fromisoformat(row[0].strip())
        except ValueError:
            continue
        if len(row) < expected_columns:
            raise CafciProviderError(
                f"CAFCI devolvió una fila incompleta para {point_date.isoformat()}"
            )
        for column, class_id in enumerate(class_ids, start=1):
            try:
                cumulative_return = _parse_percentage(row[column])
            except CafciProviderError as exc:
                logger.warning(
                    "CAFCI: se omitió el rendimiento inválido de la clase %s "
                    "para %s: %s",
                    class_id,
                    point_date.isoformat(),
                    exc,
                )
                continue
            if cumulative_return is not None:
                series[class_id].append(
                    FciComparisonPoint(point_date, cumulative_return)
                )

    return {
        class_id: tuple(sorted(points, key=lambda point: point.quote_date))
        for class_id, points in series.items()
    }


def _parse_percentage(value: str) -> Decimal | None:
    cleaned = value.strip().replace("\xa0", " ").replace("\u2212", "-")
    if not cleaned or cleaned in {"-", "\u2013", "\u2014", "\ufffd"}:
        return None
    match = PERCENT_PATTERN.fullmatch(cleaned)
    if match is None:
        raise CafciProviderError(
            f"CAFCI devolvió un rendimiento porcentual inválido: {value!r}"
        )
    try:
        normalized = _normalize_decimal_separator(match.group(1))
        result = Decimal(normalized)
    except (InvalidOperation, ValueError) as exc:
        raise CafciProviderError(
            f"CAFCI devolvió un rendimiento porcentual inválido: {value!r}"
        ) from exc
    if not result.is_finite():
        raise CafciProviderError(
            f"CAFCI devolvió un rendimiento porcentual inválido: {value!r}"
        )
    return result


def _normalize_decimal_separator(value: str) -> str:
    sign = ""
    if value[0] in "+-":
        sign, value = value[0], value[1:]
    if not value:
        raise ValueError("el porcentaje no tiene parte numérica")

    if "." in value and "," in value:
        decimal_separator = "." if value.rfind(".") > value.rfind(",") else ","
        grouping_separator = "," if decimal_separator == "." else "."
        integer_part, fractional_part = value.rsplit(decimal_separator, 1)
        if not fractional_part.isdigit():
            raise ValueError("la parte decimal no es numérica")
        if grouping_separator in fractional_part:
            raise ValueError("separadores de miles después de la coma decimal")
        if grouping_separator in integer_part:
            groups = integer_part.split(grouping_separator)
            if not 1 <= len(groups[0]) <= 3 or any(len(group) != 3 for group in groups[1:]):
                raise ValueError("separador de miles inválido")
            integer_part = "".join(groups)
        if not integer_part.isdigit():
            raise ValueError("la parte entera no es numérica")
        return f"{sign}{integer_part}.{fractional_part}"

    separator = "." if "." in value else "," if "," in value else None
    if separator is None:
        if not value.isdigit():
            raise ValueError("la parte entera no es numérica")
        return f"{sign}{value}"

    groups = value.split(separator)
    if len(groups) == 2:
        if not all(group.isdigit() for group in groups):
            raise ValueError("el porcentaje contiene caracteres inválidos")
        return f"{sign}{groups[0]}.{groups[1]}"
    if not all(group.isdigit() for group in groups):
        raise ValueError("el porcentaje contiene caracteres inválidos")
    if not 1 <= len(groups[0]) <= 3:
        raise ValueError("el agrupamiento de miles es inválido")
    if all(len(group) == 3 for group in groups[1:]):
        return f"{sign}{''.join(groups)}"
    if (
        all(len(group) == 3 for group in groups[1:-1])
        and len(groups[-1]) in (1, 2)
    ):
        return f"{sign}{''.join(groups[:-1])}.{groups[-1]}"
    raise ValueError("formato numérico con separadores inválido")


def reconstruct_nav_points(
    current_price: Decimal,
    comparison_points: Sequence[FciComparisonPoint],
    current_quote_date: date,
) -> tuple[FciHistoricalPoint, ...]:
    if not comparison_points:
        return ()
    ordered = sorted(comparison_points, key=lambda point: point.quote_date)
    if ordered[-1].quote_date != current_quote_date:
        return ()
    final_factor = Decimal("1") + ordered[-1].cumulative_return / Decimal("100")
    if final_factor <= 0:
        raise CafciProviderError("El rendimiento de CAFCI produce un valor final inválido")

    first_allowed_date = current_quote_date - timedelta(days=365)
    points = []
    for comparison_point in ordered:
        if comparison_point.quote_date < first_allowed_date:
            continue
        factor = Decimal("1") + comparison_point.cumulative_return / Decimal("100")
        price = (current_price * factor / final_factor).quantize(PRICE_QUANTUM)
        if price <= 0:
            raise CafciProviderError("CAFCI produjo una cuotaparte histórica no positiva")
        points.append(FciHistoricalPoint(comparison_point.quote_date, price))
    return tuple(points)


def _interpolated_price(
    target_date: date,
    points: Sequence[FciHistoricalPoint],
) -> Decimal | None:
    for point in points:
        if target_date == point.quote_date:
            return point.price
    for left, right in zip(points, points[1:]):
        gap_days = (right.quote_date - left.quote_date).days
        if (
            left.quote_date < target_date < right.quote_date
            and gap_days <= MAX_INTERPOLATION_GAP_DAYS
        ):
            elapsed_days = (target_date - left.quote_date).days
            return left.price + (
                (right.price - left.price) * Decimal(elapsed_days) / Decimal(gap_days)
            )
    return None


def _relative_deviation(value: Decimal, expected: Decimal) -> Decimal:
    return abs(value - expected) / expected


def _read_url(opener, url: str, referer: str | None = None) -> tuple[bytes, str]:
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/json,*/*",
    }
    if referer is not None:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    max_retries = max(
        len(COMPARATOR_RETRY_DELAYS_SECONDS),
        len(COMPARATOR_FORBIDDEN_RETRY_DELAYS_SECONDS),
    )
    for attempt in range(max_retries + 1):
        try:
            with opener.open(request, timeout=CAFCI_TIMEOUT_SECONDS) as response:
                content = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return content, charset
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504):
                if exc.code != 403:
                    raise CafciProviderError(
                        f"CAFCI respondió HTTP {exc.code} al consultar el comparador"
                    ) from exc
                retry_delays = COMPARATOR_FORBIDDEN_RETRY_DELAYS_SECONDS
            else:
                retry_delays = COMPARATOR_RETRY_DELAYS_SECONDS
            if attempt == len(retry_delays):
                raise CafciProviderError(
                    f"CAFCI mantuvo HTTP {exc.code} tras varios reintentos"
                ) from exc
            time.sleep(retry_delays[attempt])
        except (URLError, TimeoutError, OSError) as exc:
            if attempt == len(COMPARATOR_RETRY_DELAYS_SECONDS):
                raise CafciProviderError(
                    "No se pudo consultar el comparador histórico de CAFCI"
                ) from exc
            time.sleep(COMPARATOR_RETRY_DELAYS_SECONDS[attempt])
    raise CafciProviderError("No se pudo consultar el comparador histórico de CAFCI")


def _create_comparator_opener():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    _read_url(opener, CAFCI_COMPARATOR_PAGE)
    return opener


def _fetch_class_to_fund_mapping(opener) -> dict[int, int]:
    content, _ = _read_url(
        opener,
        CAFCI_COMPARATOR_CATALOG,
        referer=CAFCI_COMPARATOR_PAGE,
    )
    try:
        catalog = json.loads(content)
        funds = catalog["fondos"]
        mapping: dict[int, int] = {}
        for fund in funds:
            fund_id = int(fund["id"])
            for fund_class in fund["clases"]:
                class_id = int(fund_class["id"])
                if class_id in mapping and mapping[class_id] != fund_id:
                    raise CafciProviderError(
                        f"CAFCI repitió el identificador de clase {class_id}"
                    )
                mapping[class_id] = fund_id
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, CafciProviderError):
            raise
        raise CafciProviderError(
            "CAFCI devolvió un catálogo de clases con formato inesperado"
        ) from exc
    return mapping


def _fetch_comparison_series(
    opener,
    fund_classes: Sequence[tuple[int, int]],
) -> dict[int, tuple[FciComparisonPoint, ...]]:
    class_ids = [class_id for _, class_id in fund_classes]
    selection = ",".join(
        f"{fund_id}:{class_id}" for fund_id, class_id in fund_classes
    )
    query = urlencode({
        "fondos": selection,
        "periodo": "ultimoAnio",
        "visualizacion": "tabla",
    })
    content, charset = _read_url(
        opener,
        f"{CAFCI_COMPARATOR_RESULT}?{query}",
        referer=CAFCI_COMPARATOR_PAGE,
    )
    try:
        html = content.decode(charset)
    except (LookupError, UnicodeDecodeError) as exc:
        raise CafciProviderError("CAFCI devolvió una codificación HTML inválida") from exc
    return parse_comparator_html(html, class_ids)


def _load_fci_assets() -> list[Activo]:
    db = SessionLocal()
    try:
        return db.query(Activo).filter(Activo.tipo == "fci").all()
    finally:
        db.close()


def _save_backfill_group(
    db: Session,
    series_by_asset: Sequence[
        tuple[Activo, tuple[FciHistoricalPoint, ...]]
    ],
) -> tuple[int, int, int]:
    points_added = 0
    points_corrected = 0
    suspicious_points_removed = 0
    for asset, points in series_by_asset:
        if not points:
            continue
        start_date = points[0].quote_date
        end_date = points[-1].quote_date
        records = db.query(ActivoCotizacionHistorica).filter(
            ActivoCotizacionHistorica.activo_id == asset.id,
            ActivoCotizacionHistorica.fecha >= start_date,
            ActivoCotizacionHistorica.fecha <= end_date,
        ).all()
        records_by_date = {record.fecha: record for record in records}
        point_by_date = {point.quote_date: point for point in points}

        for record in records:
            expected_price = _interpolated_price(record.fecha, points)
            if expected_price is None or expected_price <= 0:
                continue
            if _relative_deviation(Decimal(record.precio), expected_price) <= MAX_HISTORY_DEVIATION_RATIO:
                continue
            replacement = point_by_date.get(record.fecha)
            if replacement is not None:
                record.precio = replacement.price
                points_corrected += 1
            else:
                db.delete(record)
                records_by_date.pop(record.fecha, None)
                suspicious_points_removed += 1

        for point in points:
            record = records_by_date.get(point.quote_date)
            if record is None:
                db.add(ActivoCotizacionHistorica(
                    activo_id=asset.id,
                    fecha=point.quote_date,
                    precio=point.price,
                ))
                points_added += 1

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return points_added, points_corrected, suspicious_points_removed


def backfill_cafci_history(
    request_delay: float = COMPARATOR_REQUEST_DELAY_SECONDS,
    max_groups: int | None = None,
    start_group: int = 0,
) -> FciBackfillResult:
    if request_delay < 0:
        raise ValueError("request_delay no puede ser negativo")
    if start_group < 0:
        raise ValueError("start_group no puede ser negativo")
    if max_groups is not None and max_groups < 0:
        raise ValueError("max_groups no puede ser negativo")

    quotes = fetch_cafci_quotes()
    db = SessionLocal()
    try:
        inserted_quotes, updated_quotes = sync_cafci_quotes(db, quotes)
    finally:
        db.close()
    logger.info(
        "CAFCI: %s FCI nuevos y %s cotizaciones actualizadas antes del backfill",
        inserted_quotes,
        updated_quotes,
    )

    assets = _load_fci_assets()
    assets_by_code: dict[int, Activo] = {}
    for asset in assets:
        match = TICKER_CODE_PATTERN.fullmatch(asset.ticker)
        if match is not None:
            assets_by_code[int(match.group(1))] = asset
    quotes_by_ticker = {quote.ticker: quote for quote in quotes}

    opener = _create_comparator_opener()
    class_to_fund = _fetch_class_to_fund_mapping(opener)
    missing_mapping_count = sum(
        1 for class_id in assets_by_code if class_id not in class_to_fund
    )
    assets_without_quote = 0
    fund_classes: list[tuple[int, int, Activo, FciQuote]] = []
    for class_id, asset in sorted(assets_by_code.items()):
        fund_id = class_to_fund.get(class_id)
        if fund_id is None:
            continue
        quote = quotes_by_ticker.get(asset.ticker)
        if quote is None:
            assets_without_quote += 1
            continue
        fund_classes.append((fund_id, class_id, asset, quote))

    assets_without_usable_series = 0
    assets_backfilled = 0
    points_added = 0
    points_corrected = 0
    suspicious_points_removed = 0
    total_group_count = (
        len(fund_classes) + COMPARATOR_MAX_FUNDS - 1
    ) // COMPARATOR_MAX_FUNDS
    group_end = total_group_count
    if max_groups is not None:
        group_end = min(total_group_count, start_group + max_groups)
    if start_group > total_group_count:
        raise ValueError("start_group supera la cantidad total de lotes")
    db = SessionLocal()
    try:
        for group_index in range(start_group, group_end):
            group = fund_classes[
                group_index * COMPARATOR_MAX_FUNDS:
                (group_index + 1) * COMPARATOR_MAX_FUNDS
            ]
            requested_classes = [(fund_id, class_id) for fund_id, class_id, _, _ in group]
            comparison_series = _fetch_comparison_series(opener, requested_classes)
            ready_series = []
            for _, class_id, asset, quote in group:
                history = reconstruct_nav_points(
                    quote.price,
                    comparison_series.get(class_id, ()),
                    quote.quote_date,
                )
                if not history:
                    assets_without_usable_series += 1
                    continue
                ready_series.append((asset, history))
                assets_backfilled += 1
            added, corrected, removed = _save_backfill_group(db, ready_series)
            points_added += added
            points_corrected += corrected
            suspicious_points_removed += removed
            if request_delay:
                time.sleep(request_delay)
            if (
                (group_index + 1) % COMPARATOR_COOLDOWN_EVERY_GROUPS == 0
                and group_index + 1 < group_end
            ):
                logger.info(
                    "CAFCI: pausa de cortesía tras el lote %s",
                    group_index + 1,
                )
                time.sleep(COMPARATOR_COOLDOWN_SECONDS)
            if (group_index + 1) % 25 == 0 or group_index + 1 == group_end:
                logger.info(
                    "CAFCI: grupos %s/%s; FCI con historial %s; puntos nuevos %s",
                    group_index + 1,
                    total_group_count,
                    assets_backfilled,
                    points_added,
                )
    finally:
        db.close()

    result = FciBackfillResult(
        assets_found=len(assets),
        assets_backfilled=assets_backfilled,
        assets_without_comparator_mapping=missing_mapping_count,
        assets_without_quote=assets_without_quote,
        assets_without_usable_series=assets_without_usable_series,
        points_added=points_added,
        points_corrected=points_corrected,
        suspicious_points_removed=suspicious_points_removed,
    )
    logger.info("Resultado del backfill CAFCI: %s", result)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Completa el historial de FCI desde CAFCI")
    parser.add_argument(
        "--start-group",
        type=int,
        default=0,
        help="índice cero-based del lote desde el que reanudar",
    )
    args = parser.parse_args()
    backfill_cafci_history(start_group=args.start_group)


if __name__ == "__main__":
    main()
