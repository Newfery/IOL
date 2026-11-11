from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Literal


class CreateActivoSchema(BaseModel):  # POST
    ticker: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    tipo: Literal["accion", "cedear", "bono"]
    moneda: Literal["ARS", "USD"]
    precio_actual: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    nivel_riesgo: int = Field(ge=1, le=5)
    activo: bool = True


class UpdateActivoSchema(BaseModel):  # PUT/PATCH
    ticker: str | None = Field(default=None, min_length=1, max_length=20)
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    tipo: Literal["accion", "cedear", "bono"] | None = None
    moneda: Literal["ARS", "USD"] | None = None
    precio_actual: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=2)
    nivel_riesgo: int | None = Field(default=None, ge=1, le=5)
    activo: bool | None = None


class DeleteActivoSchema(BaseModel):  # DELETE
    id: int


class GetActivoSchema(BaseModel):  # GET
    id: int