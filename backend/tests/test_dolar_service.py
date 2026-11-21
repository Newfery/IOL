import unittest
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from src.services.dolar_service import DolarQuoteError, DolarQuoteService


class DolarQuoteServiceTests(unittest.TestCase):
    @patch("src.services.dolar_service.urlopen")
    def test_reads_sale_rate_from_dolar_api(self, urlopen_mock):
        urlopen_mock.return_value = BytesIO(b'{"venta": 1743.10}')

        quote = DolarQuoteService.obtener("mep")

        self.assertEqual(quote, Decimal("1743.1"))
        request = urlopen_mock.call_args.args[0]
        self.assertEqual(request.full_url, "https://dolarapi.com/v1/dolares/bolsa")
        self.assertEqual(request.get_header("Accept"), "application/json")
        self.assertEqual(
            request.get_header("User-agent"),
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
        )
        self.assertEqual(urlopen_mock.call_args.kwargs, {"timeout": 5})

    @patch("src.services.dolar_service.urlopen")
    def test_rejects_missing_or_invalid_sale_rate(self, urlopen_mock):
        urlopen_mock.return_value = BytesIO(b'{"compra": 1700}')

        with self.assertRaises(DolarQuoteError):
            DolarQuoteService.obtener("ccl")

    @patch("src.services.dolar_service.urlopen")
    def test_translates_network_failure_to_quote_error(self, urlopen_mock):
        urlopen_mock.side_effect = TimeoutError("offline")

        with self.assertRaises(DolarQuoteError):
            DolarQuoteService.obtener("mep")


if __name__ == "__main__":
    unittest.main()
