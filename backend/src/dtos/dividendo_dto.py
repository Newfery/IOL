from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateDividendoDTO(BaseModel):
    activo_id: int = Field(gt=0)
    monto_por_unidad: Decimal = Field(gt=0)
    fecha_pago: datetime


class DividendoResponseDTO(BaseModel):
    id: int
    activo_id: int
    monto_por_unidad: Decimal
    fecha_pago: datetime

    model_config = {"from_attributes": True}
