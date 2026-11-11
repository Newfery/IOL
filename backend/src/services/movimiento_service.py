from sqlalchemy.orm import Session

from src.dtos.movimiento_dto import (
    CreateMovimientoDTO,
    MovimientoResponseDTO,
    UpdateMovimientoDTO,
)
from src.mappers.movimiento_mapper import to_movimiento_response
from src.repositories.movimiento_repository import MovimientoRepository


class MovimientoService:
    def __init__(self, db: Session):
        self.repo = MovimientoRepository(db)

    def create(self, dto: CreateMovimientoDTO) -> MovimientoResponseDTO:
        movimiento = self.repo.create(
            cuenta_id=dto.cuenta_id,
            tipo=dto.tipo,
            moneda=dto.moneda,
            monto=dto.monto,
            descripcion=dto.descripcion,
        )
        return to_movimiento_response(movimiento)

    def get_by_id(self, movimiento_id: int) -> MovimientoResponseDTO | None:
        movimiento = self.repo.find_by_id(movimiento_id)
        if movimiento is None:
            return None
        return to_movimiento_response(movimiento)

    def list_all(self) -> list[MovimientoResponseDTO]:
        return [
            to_movimiento_response(movimiento)
            for movimiento in self.repo.list_all()
        ]

    def update(
        self,
        movimiento_id: int,
        dto: UpdateMovimientoDTO,
    ) -> MovimientoResponseDTO | None:
        fields: dict[str, object] = dto.model_dump(exclude_unset=True)
        movimiento = self.repo.update(movimiento_id, **fields)
        if movimiento is None:
            return None
        return to_movimiento_response(movimiento)

    def delete(self, movimiento_id: int) -> bool:
        return self.repo.delete(movimiento_id)
