from pydantic import BaseModel


class CreateFavoritoDTO(BaseModel):
    inversor_id: int
    activo_id: int


class FavoritoResponseDTO(BaseModel):
    inversor_id: int
    activo_id: int

    model_config = {"from_attributes": True}
