from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class CreateGrupoDeInversionSchema(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    codigo_union: str = Field(min_length=1, max_length=50)
    creador_id: int = Field(gt=0)
    plata_disponible: Decimal = Field(default=Decimal("0.00"), ge=0)


class UpdateGrupoDeInversionSchema(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    codigo_union: str | None = Field(default=None, min_length=1, max_length=50)
    creador_id: int | None = Field(default=None, gt=0)
    plata_disponible: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        if isinstance(values, dict) and any(value is None for value in values.values()):
            raise ValueError("Los campos enviados no pueden ser null")
        return values
