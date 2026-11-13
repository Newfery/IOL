from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# DTO para crear una operación
class OperacionCreate(BaseModel):

    cuenta_id: int
    activo_id: int

    tipo: str = Field(..., pattern="^(compra|venta)$")
    cantidad: Decimal = Field(..., gt=0, max_digits=18, decimal_places=4)


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