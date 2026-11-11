import unittest
from decimal import Decimal
from unittest.mock import patch

import pandas as pd

from src.services.cotizacion_service import (
    CotizacionProviderError,
    CotizacionService,
)
from src.utils.errors import NotFoundError


class CotizacionServiceTests(unittest.TestCase):
    @patch("src.services.cotizacion_service.yf.Ticker")
    def test_obtener_devuelve_ultimo_cierre_y_variacion(self, ticker_mock):
        ticker_mock.return_value.history.return_value = pd.DataFrame(
            {"Close": [100.0, 110.0]},
            index=pd.to_datetime(["2026-11-10", "2026-11-11"]),
        )

        cotizacion = CotizacionService.obtener("aapl")

        self.assertEqual(cotizacion.ticker, "AAPL")
        self.assertEqual(cotizacion.precio, Decimal("110.0"))
        self.assertEqual(cotizacion.cierre_anterior, Decimal("100.0"))
        self.assertEqual(cotizacion.variacion_porcentual, Decimal("10.0"))

    @patch("src.services.cotizacion_service.yf.Ticker")
    def test_obtener_rechaza_tickers_sin_datos(self, ticker_mock):
        ticker_mock.return_value.history.return_value = pd.DataFrame()

        with self.assertRaises(NotFoundError):
            CotizacionService.obtener("INVALID")

    @patch("src.services.cotizacion_service.yf.Ticker")
    def test_obtener_sin_cierre_anterior_devuelve_variacion_nula(self, ticker_mock):
        ticker_mock.return_value.history.return_value = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2026-11-11"]),
        )

        cotizacion = CotizacionService.obtener("AAPL")

        self.assertIsNone(cotizacion.cierre_anterior)
        self.assertIsNone(cotizacion.variacion_porcentual)

    @patch("src.services.cotizacion_service.yf.Ticker")
    def test_obtener_expone_error_del_proveedor(self, ticker_mock):
        ticker_mock.return_value.history.side_effect = RuntimeError("offline")

        with self.assertLogs("src.services.cotizacion_service", level="ERROR"):
            with self.assertRaises(CotizacionProviderError):
                CotizacionService.obtener("AAPL")


if __name__ == "__main__":
    unittest.main()
