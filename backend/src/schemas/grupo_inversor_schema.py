from datetime import datetime

from pydantic import BaseModel, Field


class CreateGrupoInversorSchema(BaseModel):
    inversor_id: int = Field(gt=0)
    fecha_union: datetime | None = None
