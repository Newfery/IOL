import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.routers.dashboard_router import market_dolar
from src.services.dolar_service import DolarQuoteError


class MarketDolarTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.query.return_value.filter.return_value.all.return_value = []

    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_uses_dolar_api_when_local_bond_quotes_are_missing(self, quote_mock):
        quote_mock.side_effect = [Decimal("1250.50"), Decimal("1300.25")]

        result = market_dolar(self.db)

        self.assertEqual(result, {"mep": 1250.5, "ccl": 1300.25})
        self.assertEqual(
            [call.args[0] for call in quote_mock.call_args_list],
            ["mep", "ccl"],
        )

    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_keeps_mep_when_ccl_provider_fails(self, quote_mock):
        quote_mock.side_effect = [Decimal("1250.50"), DolarQuoteError("offline")]

        result = market_dolar(self.db)

        self.assertEqual(result, {"mep": 1250.5, "ccl": None})


if __name__ == "__main__":
    unittest.main()
