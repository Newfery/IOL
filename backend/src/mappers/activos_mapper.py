from src.db.models.activos_model import Activo
from src.dtos.activo_dto import CreateActivoDTO, ActivoResponseDTO


def activo_a_dto(activo: Activo) -> ActivoResponseDTO:
    return ActivoResponseDTO.model_validate(activo)


def dto_a_activo(datos: CreateActivoDTO) -> Activo:
    return Activo(**datos.model_dump())