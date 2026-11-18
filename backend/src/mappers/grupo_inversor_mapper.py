from src.db.models.grupo_inversor_model import GrupoInversor
from src.dtos.grupo_inversor_dto import GrupoInversorResponseDTO


def to_grupo_inversor_response(
    integrante: GrupoInversor,
) -> GrupoInversorResponseDTO:
    return GrupoInversorResponseDTO.model_validate(integrante)
