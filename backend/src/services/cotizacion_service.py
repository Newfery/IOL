import logging
from decimal import Decimal

import yfinance as yf

from src.dtos.cotizacion_dto import CotizacionResponseDTO
from src.utils.errors import AppError, NotFoundError

logger = logging.getLogger(__name__)


class CotizacionProviderError(AppError):
    status_code = 502
    message = "No se pudo consultar el proveedor de cotizaciones"


class CotizacionService:
    @staticmethod
    def obtener(ticker: str) -> CotizacionResponseDTO:
        symbol = ticker.strip().upper()

        try:
            history = yf.Ticker(symbol).history(
                period="5d",
                interval="1d",
                auto_adjust=False,
            )
        except Exception as exc:
            logger.exception("Error consultando cotización para %s", symbol)
            raise CotizacionProviderError() from exc

        if history.empty or "Close" not in history:
            raise NotFoundError(f"No se encontraron cotizaciones para {symbol}")

        cierres = history["Close"].dropna()
        if cierres.empty:
            raise NotFoundError(f"No se encontraron cotizaciones para {symbol}")

        precio = Decimal(str(cierres.iloc[-1]))
        if precio <= 0:
            raise NotFoundError(f"No se encontraron cotizaciones para {symbol}")

        cierre_anterior = (
            Decimal(str(cierres.iloc[-2])) if len(cierres) > 1 else None
        )
        variacion = None
        if cierre_anterior is not None and cierre_anterior != 0:
            variacion = (
                (precio - cierre_anterior) / cierre_anterior * Decimal("100")
            )

        fecha = cierres.index[-1].to_pydatetime()

        return CotizacionResponseDTO(
            ticker=symbol,
            precio=precio,
            cierre_anterior=cierre_anterior,
            variacion_porcentual=variacion,
            fecha=fecha,
        )
