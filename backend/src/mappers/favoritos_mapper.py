from src.db.models.favoritos_model import Favorito
from src.dtos.favoritos_dto import FavoritoResponseDTO


def to_favorito_response(favorito: Favorito) -> FavoritoResponseDTO:
    return FavoritoResponseDTO.model_validate(favorito)
