from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateGrupoDeInversionDTO(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    codigo_union: str = Field(min_length=1, max_length=50)
    creador_id: int = Field(gt=0)
    plata_disponible: Decimal = Field(default=Decimal("0.00"), ge=0)


class UpdateGrupoDeInversionDTO(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    codigo_union: str | None = Field(default=None, min_length=1, max_length=50)
    creador_id: int | None = Field(default=None, gt=0)
    plata_disponible: Decimal | None = Field(default=None, ge=0)


class GrupoDeInversionResponseDTO(BaseModel):
    id: int
    nombre: str
    codigo_union: str
    creador_id: int
    plata_disponible: Decimal
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
