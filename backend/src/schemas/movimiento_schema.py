from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CreateMovimientoSchema(BaseModel):
    cuenta_id: int = Field(gt=0)
    tipo: Literal["deposito", "extraccion"]
    moneda: Literal["ARS", "USD"]
    monto: Decimal = Field(gt=0)
    descripcion: str | None = None


class UpdateMovimientoSchema(BaseModel):
    cuenta_id: int | None = Field(default=None, gt=0)
    tipo: Literal["deposito", "extraccion", "dividendo"] | None = None
    moneda: Literal["ARS", "USD"] | None = None
    monto: Decimal | None = Field(default=None, gt=0)
    descripcion: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        if isinstance(values, dict) and any(
            value is None for key, value in values.items() if key != "descripcion"
        ):
            raise ValueError("Los campos enviados no pueden ser null")
        return values
