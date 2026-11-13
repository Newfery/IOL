from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CotizacionResponseDTO(BaseModel):
    ticker: str
    precio: Decimal
    cierre_anterior: Decimal | None
    variacion_porcentual: Decimal | None
    fecha: datetime
