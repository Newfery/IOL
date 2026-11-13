from pydantic import BaseModel, Field


class CreateFavoritoSchema(BaseModel):
    inversor_id: int = Field(gt=0)
    activo_id: int = Field(gt=0)
