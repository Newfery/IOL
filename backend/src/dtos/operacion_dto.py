from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# DTO para crear una operación
class OperacionCreate(BaseModel):

    cuenta_id: int
    activo_id: int

    tipo: str = Field(..., pattern="^(compra|venta)$")

    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0)

    comision: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., gt=0)

    estado: str = Field(
        default="pendiente",
        pattern="^(pendiente|ejecutada|rechazada)$"
    )


# DTO para devolver una operación
class OperacionResponse(BaseModel):

    id: int
    cuenta_id: int
    activo_id: int

    tipo: str
    cantidad: Decimal
    precio_unitario: Decimal

    comision: Decimal
    total: Decimal

    resultado_realizado: Optional[Decimal] = None

    fecha: datetime
    estado: str

    class Config:
        from_attributes = True