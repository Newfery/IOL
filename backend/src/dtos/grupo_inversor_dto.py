from datetime import datetime

from pydantic import BaseModel, Field


class CreateGrupoInversorDTO(BaseModel):
    grupo_id: int = Field(gt=0)
    inversor_id: int = Field(gt=0)
    fecha_union: datetime | None = None


class GrupoInversorResponseDTO(BaseModel):
    grupo_id: int
    inversor_id: int
    fecha_union: datetime

    model_config = {"from_attributes": True}
