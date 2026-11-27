import unittest
from unittest.mock import call, patch

from src.services.finnhub_service import (
    _asset_type,
    _normalize_ticker,
    fetch_finnhub_assets,
)


class FinnhubServiceTests(unittest.TestCase):
    def test_asset_type_maps_supported_database_types(self):
        self.assertEqual(_asset_type("Common Stock"), "accion")
        self.assertEqual(_asset_type("ETP"), "etf")
        self.assertEqual(_asset_type("American Depositary Receipt"), "accion")
        self.assertIsNone(_asset_type("Bond"))

    def test_us_ticker_is_namespaced(self):
        self.assertEqual(_normalize_ticker("AAPL", "US"), "AAPL.US")
        self.assertEqual(_normalize_ticker("AAPL.US", "US"), "AAPL.US")

    def test_argentine_ticker_removes_market_suffix(self):
        self.assertEqual(_normalize_ticker("GGAL.BA", "BUE"), "GGAL")

    @patch("src.services.finnhub_service.time.sleep")
    @patch("src.services.finnhub_service.finnhub.Client")
    def test_fetch_skips_existing_assets_and_throttles_every_quote(
        self,
        client_class,
        sleep,
    ):
        client = client_class.return_value
        client.stock_symbols.return_value = [
            {
                "symbol": "EXIST",
                "currency": "USD",
                "mic": "XNAS",
                "type": "Common Stock",
                "description": "Already added",
            },
            {
                "symbol": "NOQUOTE",
                "currency": "USD",
                "mic": "XNYS",
                "type": "Common Stock",
                "description": "No current quote",
            },
            {
                "symbol": "NEW",
                "currency": "USD",
                "mic": "XNAS",
                "type": "Common Stock",
                "description": "New asset",
            },
        ]
        client.quote.side_effect = [
            {"c": 0},
            {"c": 12.5, "dp": 1.25, "t": 1795640400},
        ]

        assets = fetch_finnhub_assets(
            limit=1,
            excluded_tickers={"EXIST.US"},
        )

        self.assertEqual([asset.ticker for asset in assets], ["NEW.US"])
        self.assertEqual(
            client.quote.call_args_list,
            [call("NOQUOTE"), call("NEW")],
        )
        self.assertEqual(sleep.call_count, 2)

