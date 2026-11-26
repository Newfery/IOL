import unittest
from unittest.mock import patch

from src.db.seeders.yfinance_assets import (
    CATALOG,
    US_EQUITY_PAGE_SIZE,
    fetch_us_equities,
)


class YahooAssetCatalogTests(unittest.TestCase):
    def test_disney_cedear_uses_the_current_market_ticker(self):
        disney = next(asset for asset in CATALOG if asset[2] == "Disney (CEDEAR)")

        self.assertEqual(disney[:2], ("DISN", "DISN.BA"))

    @patch("src.db.seeders.yfinance_assets.yf.screen")
    def test_fetch_us_equities_paginates_and_namespaces_us_symbols(self, screen):
        def quote(symbol: str, quote_type: str = "EQUITY") -> dict[str, object]:
            return {
                "symbol": symbol,
                "shortName": symbol,
                "quoteType": quote_type,
                "currency": "USD",
                "regularMarketPrice": 10,
                "regularMarketChangePercent": 2.5,
            }

        screen.side_effect = [
            {"total": US_EQUITY_PAGE_SIZE + 1, "quotes": [
                quote(f"TEST{index}") for index in range(US_EQUITY_PAGE_SIZE)
            ]},
            {"total": US_EQUITY_PAGE_SIZE + 1, "quotes": [quote("LAST", "ETF")]},
        ]

        assets = fetch_us_equities()

        self.assertEqual(len(assets), US_EQUITY_PAGE_SIZE + 1)
        self.assertEqual(assets[0].ticker, "TEST0.US")
        self.assertEqual(assets[0].currency, "USD")
        self.assertEqual(assets[-1].asset_type, "etf")
        self.assertEqual(screen.call_args_list[1].kwargs["offset"], US_EQUITY_PAGE_SIZE)


if __name__ == "__main__":
    unittest.main()
