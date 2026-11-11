from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Schema para crear una operación
class OperacionSchemaCreate(BaseModel):

    cuenta_id: int
    activo_id: int

    tipo: str = Field(..., pattern="^(compra|venta)$")

    cantidad: Decimal = Field(..., gt=0)


# Schema para devolver una operación
class OperacionSchemaResponse(BaseModel):

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

    # Permite convertir objetos de SQLAlchemy en schemas
    model_config = ConfigDict(from_attributes=True)