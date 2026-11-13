from src.db.models.dividendo_model import Dividendo
from src.dtos.dividendo_dto import DividendoResponseDTO


def to_dividendo_response(dividendo: Dividendo) -> DividendoResponseDTO:
    return DividendoResponseDTO.model_validate(dividendo)
