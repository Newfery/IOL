import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_QUOTE_URLS = {
    "mep": "https://dolarapi.com/v1/dolares/bolsa",
    "ccl": "https://dolarapi.com/v1/dolares/contadoconliqui",
}


class DolarQuoteError(Exception):
    pass


class DolarQuoteService:
    @staticmethod
    def obtener(quote_type: Literal["mep", "ccl"]) -> Decimal:
        url = _QUOTE_URLS[quote_type]
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                ),
            },
        )
        try:
            with urlopen(request, timeout=5) as response:
                payload = json.load(response)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            logger.warning("Error consultando cotización en %s: %s", url, exc)
            message = f"No se pudo consultar la fuente para {quote_type.upper()}"
            raise DolarQuoteError(message) from exc

        try:
            price = Decimal(str(payload["venta"]))
        except (KeyError, TypeError, InvalidOperation) as exc:
            message = f"La fuente devolvió una cotización inválida para {quote_type.upper()}"
            raise DolarQuoteError(message) from exc
        if not price.is_finite() or price <= 0:
            message = f"La fuente devolvió una cotización inválida para {quote_type.upper()}"
            raise DolarQuoteError(message)
        return price
