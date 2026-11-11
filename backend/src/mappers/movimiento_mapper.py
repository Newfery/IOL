from src.db.models.movimiento_model import Movimiento
from src.dtos.movimiento_dto import MovimientoResponseDTO


def to_movimiento_response(movimiento: Movimiento) -> MovimientoResponseDTO:
    return MovimientoResponseDTO.model_validate(movimiento)
