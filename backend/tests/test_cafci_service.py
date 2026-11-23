from datetime import date
from decimal import Decimal
from io import BytesIO
import unittest

from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.activos_model import Activo
from src.db.models.activo_cotizacion_historica_model import ActivoCotizacionHistorica
from src.routers.dashboard_router import market_asset_history
from src.services.cafci_service import (
    FciQuote,
    parse_cafci_workbook,
    sync_cafci_quotes,
)


def make_workbook(rows: list[tuple[object, ...]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row_number in range(1, 10):
        worksheet.cell(row=row_number, column=1, value=f"header {row_number}")
    worksheet.cell(row=9, column=7, value="19/11/2026")
    for row_number, row in enumerate(rows, start=10):
        for column_number, value in enumerate(row, start=1):
            worksheet.cell(row=row_number, column=column_number, value=value)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def cafci_row(
    *,
    name: str = "Fondo de prueba",
    currency: str = "ARS",
    quote_date: str = "20/11/2026",
    price: float = 123.4567,
    change: float = 0.25,
    code: int = 1234,
) -> tuple[object, ...]:
    row: list[object] = [None] * 21
    row[0] = name
    row[1] = currency
    row[4] = quote_date
    row[5] = price
    row[6] = 123.4
    row[7] = change
    row[20] = code
    return tuple(row)


class CafciServiceTests(unittest.TestCase):
    def test_parse_cafci_workbook_keeps_nav_precision_and_quote_date(self):
        quotes = parse_cafci_workbook(make_workbook([cafci_row()]))

        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].ticker, "FCI-1234")
        self.assertEqual(quotes[0].currency, "ARS")
        self.assertEqual(quotes[0].price, Decimal("123.456700"))
        self.assertEqual(quotes[0].quote_date, date(2026, 11, 20))
        self.assertEqual(quotes[0].previous_price, Decimal("123.400000"))
        self.assertEqual(quotes[0].previous_quote_date, date(2026, 11, 19))

    def test_parse_cafci_workbook_includes_ars_and_usd_funds(self):
        quotes = parse_cafci_workbook(make_workbook([
            cafci_row(code=1234, currency="ARS"),
            cafci_row(code=5678, currency="USD"),
        ]))

        self.assertEqual({quote.currency for quote in quotes}, {"ARS", "USD"})

    def test_parse_cafci_workbook_rejects_duplicate_provider_codes(self):
        with self.assertRaisesRegex(RuntimeError, "duplicado"):
            parse_cafci_workbook(make_workbook([
                cafci_row(code=1234),
                cafci_row(code=1234, name="Otro nombre"),
            ]))

    def test_sync_saves_one_history_point_per_date_and_endpoint_returns_it(self):
        engine = create_engine("sqlite:///:memory:")
        Activo.__table__.create(engine)
        ActivoCotizacionHistorica.__table__.create(engine)
        db = sessionmaker(bind=engine)()
        try:
            quote = FciQuote(
                ticker="FCI-1234",
                name="Fondo de prueba",
                currency="ARS",
                price=Decimal("123.456700"),
                change=Decimal("0.25"),
                quote_date=date(2026, 11, 20),
                previous_price=Decimal("122.000000"),
                previous_quote_date=date(2026, 11, 19),
            )
            inserted, updated = sync_cafci_quotes(db, [quote])
            self.assertEqual((inserted, updated), (1, 0))

            same_day_update = FciQuote(
                ticker=quote.ticker,
                name=quote.name,
                currency=quote.currency,
                price=Decimal("124.000000"),
                change=Decimal("0.44"),
                quote_date=quote.quote_date,
                previous_price=Decimal("123.000000"),
                previous_quote_date=quote.previous_quote_date,
            )
            sync_cafci_quotes(db, [same_day_update])

            next_day = FciQuote(
                ticker=quote.ticker,
                name=quote.name,
                currency=quote.currency,
                price=Decimal("125.000000"),
                change=Decimal("0.81"),
                quote_date=date(2026, 11, 23),
                previous_price=Decimal("124.000000"),
                previous_quote_date=date(2026, 11, 20),
            )
            sync_cafci_quotes(db, [next_day])

            history = market_asset_history("FCI-1234", db)
            self.assertEqual(len(history), 3)
            self.assertEqual(history[0]["date"], "2026-11-19")
            self.assertEqual(history[0]["price"], 123.0)
            self.assertEqual(history[1]["date"], "2026-11-20")
            self.assertEqual(history[1]["price"], 124.0)
            self.assertEqual(history[2]["date"], "2026-11-23")
            self.assertEqual(
                db.query(Activo).filter(Activo.ticker == "FCI-1234").one().precio_actual,
                Decimal("125.000000"),
            )
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
