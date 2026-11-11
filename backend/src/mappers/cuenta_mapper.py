from src.db.models.cuenta_model import Cuenta
from src.dtos.cuenta_dto import CuentaResponseDTO


def to_cuenta_response(cuenta: Cuenta) -> CuentaResponseDTO:
    return CuentaResponseDTO.model_validate(cuenta)
