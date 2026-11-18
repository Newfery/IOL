from pydantic import BaseModel, Field
from decimal import Decimal


class CreateTenenciaGrupoSchema(BaseModel):
    grupo_id: int
    activo_id: int
    cantidad: Decimal = Field(gt=0)
    precio_promedio: Decimal = Field(ge=0)


class UpdateTenenciaGrupoSchema(BaseModel):
    cantidad: Decimal | None = Field(default=None, gt=0)
    precio_promedio: Decimal | None = Field(default=None, ge=0)


class DeleteTenenciaGrupoSchema(BaseModel):
    grupo_id: int
    activo_id: int


class GetTenenciaGrupoSchema(BaseModel):
    grupo_id: int
    activo_id: int