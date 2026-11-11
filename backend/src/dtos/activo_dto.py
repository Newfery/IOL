from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Literal


class CreateActivoDTO(BaseModel):
    ticker: str
    nombre: str
    tipo: Literal["accion", "cedear", "bono"]
    moneda: Literal["ARS", "USD"]
    precio_actual: Decimal = Field(gt=0)
    nivel_riesgo: int = Field(ge=1, le=5)
    activo: bool = True


class UpdateActivoDTO(BaseModel):
    ticker: str | None = None
    nombre: str | None = None
    tipo: Literal["accion", "cedear", "bono"] | None = None
    moneda: Literal["ARS", "USD"] | None = None
    precio_actual: Decimal | None = Field(default=None, gt=0)
    nivel_riesgo: int | None = Field(default=None, ge=1, le=5)
    activo: bool | None = None


class DeleteActivoDTO(BaseModel):
    id: int


class GetActivoDTO(BaseModel):
    id: int


class ActivoResponseDTO(BaseModel):
    id: int
    ticker: str
    nombre: str
    tipo: str
    moneda: str
    precio_actual: Decimal
    nivel_riesgo: int
    activo: bool

    model_config = {"from_attributes": True}