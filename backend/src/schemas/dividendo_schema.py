from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateDividendoSchema(BaseModel):
    activo_id: int = Field(gt=0)
    monto_por_unidad: Decimal = Field(gt=0)
    fecha_pago: datetime
