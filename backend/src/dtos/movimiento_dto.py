from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CreateMovimientoDTO(BaseModel):  # POST
    cuenta_id: int
    tipo: Literal["deposito", "extraccion", "dividendo"]
    moneda: Literal["ARS", "USD"]
    monto: Decimal = Field(gt=0)
    descripcion: str | None = None


class UpdateMovimientoDTO(BaseModel):  # PUT/PATCH
    cuenta_id: int | None = None
    tipo: Literal["deposito", "extraccion", "dividendo"] | None = None
    moneda: Literal["ARS", "USD"] | None = None
    monto: Decimal | None = Field(default=None, gt=0)
    descripcion: str | None = None


class DeleteMovimientoDTO(BaseModel):  # DELETE
    id: int


class GetMovimientoDTO(BaseModel):  # GET (individual)
    id: int


class MovimientoResponseDTO(BaseModel):
    id: int
    cuenta_id: int
    tipo: Literal["deposito", "extraccion", "dividendo"]
    moneda: Literal["ARS", "USD"]
    monto: Decimal
    fecha: datetime
    descripcion: str | None = None

    model_config = {"from_attributes": True}
