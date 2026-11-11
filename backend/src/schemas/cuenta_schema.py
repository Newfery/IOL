from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class CreateCuentaSchema(BaseModel):
    inversor_id: int = Field(gt=0)
    numero_comitente: str = Field(min_length=1, max_length=50)
    saldo_ars: Decimal = Field(default=Decimal("0.00"), ge=0)
    saldo_usd: Decimal = Field(default=Decimal("0.00"), ge=0)


class UpdateCuentaSchema(BaseModel):
    inversor_id: int | None = Field(default=None, gt=0)
    numero_comitente: str | None = Field(default=None, min_length=1, max_length=50)
    saldo_ars: Decimal | None = Field(default=None, ge=0)
    saldo_usd: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        if isinstance(values, dict) and any(value is None for value in values.values()):
            raise ValueError("Los campos enviados no pueden ser null")
        return values
