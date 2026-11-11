from decimal import Decimal

from sqlalchemy.orm import Session

from src.dtos.cuenta_dto import (
    CreateCuentaDTO,
    CuentaResponseDTO,
    UpdateCuentaDTO,
)
from src.mappers.cuenta_mapper import to_cuenta_response
from src.repositories.cuenta_repository import CuentaRepository


class CuentaService:
    def __init__(self, db: Session):
        self.repo = CuentaRepository(db)

    def create(self, dto: CreateCuentaDTO) -> CuentaResponseDTO:
        cuenta = self.repo.create(
            inversor_id=dto.inversor_id,
            numero_comitente=dto.numero_comitente,
            saldo_ars=dto.saldo_ars,
            saldo_usd=dto.saldo_usd,
        )
        return to_cuenta_response(cuenta)

    def get_by_id(self, cuenta_id: int) -> CuentaResponseDTO | None:
        cuenta = self.repo.find_by_id(cuenta_id)
        if cuenta is None:
            return None
        return to_cuenta_response(cuenta)

    def list_all(self) -> list[CuentaResponseDTO]:
        return [
            to_cuenta_response(cuenta)
            for cuenta in self.repo.list_all()
        ]

    def update(
        self,
        cuenta_id: int,
        dto: UpdateCuentaDTO,
    ) -> CuentaResponseDTO | None:
        fields: dict[str, int | str | Decimal] = dto.model_dump(exclude_unset=True)
        cuenta = self.repo.update(cuenta_id, **fields)
        if cuenta is None:
            return None
        return to_cuenta_response(cuenta)

    def delete(self, cuenta_id: int) -> bool:
        return self.repo.delete(cuenta_id)
