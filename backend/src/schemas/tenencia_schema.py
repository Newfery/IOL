from pydantic import BaseModel, Field
from decimal import Decimal


class CreateTenenciaSchema(BaseModel):
    cuenta_id: int
    activo_id: int
    cantidad: Decimal = Field(gt=0)
    precio_promedio: Decimal = Field(ge=0)


class UpdateTenenciaSchema(BaseModel):
    cantidad: Decimal | None = Field(default=None, gt=0)
    precio_promedio: Decimal | None = Field(default=None, ge=0)


class DeleteTenenciaSchema(BaseModel):
    cuenta_id: int
    activo_id: int


class GetTenenciaSchema(BaseModel):
    cuenta_id: int
    activo_id: int