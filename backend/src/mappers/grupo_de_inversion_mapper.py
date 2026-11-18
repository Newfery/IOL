from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.dtos.grupo_de_inversion_dto import GrupoDeInversionResponseDTO


def to_grupo_de_inversion_response(
    grupo: GrupoDeInversion,
) -> GrupoDeInversionResponseDTO:
    return GrupoDeInversionResponseDTO.model_validate(grupo)
