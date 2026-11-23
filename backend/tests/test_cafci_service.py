from datetime import date
from decimal import Decimal
from io import BytesIO
import unittest
from unittest.mock import MagicMock

from openpyxl import Workbook

from src.services.cafci_service import parse_cafci_workbook, sync_cafci_quotes


def make_workbook(rows: list[tuple[object, ...]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row_number in range(1, 10):
        worksheet.cell(row=row_number, column=1, value=f"header {row_number}")
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

    def test_sync_cafci_quotes_inserts_current_value_and_date(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.one_or_none.return_value = None
        quote = parse_cafci_workbook(make_workbook([cafci_row()]))[0]

        inserted, updated = sync_cafci_quotes(db, [quote])

        self.assertEqual((inserted, updated), (1, 0))
        inserted_asset = db.add.call_args.args[0]
        self.assertEqual(inserted_asset.tipo, "fci")
        self.assertEqual(inserted_asset.precio_actual, Decimal("123.456700"))
        self.assertEqual(inserted_asset.fecha_cotizacion, date(2026, 11, 20))
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
