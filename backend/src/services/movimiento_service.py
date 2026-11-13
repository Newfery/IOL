from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from src.dtos.movimiento_dto import (
    CreateMovimientoDTO,
    MovimientoResponseDTO,
    UpdateMovimientoDTO,
)
from src.mappers.movimiento_mapper import to_movimiento_response
from src.repositories.movimiento_repository import MovimientoRepository
from src.utils.errors import BadRequestError, ConflictError, NotFoundError


class MovimientoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MovimientoRepository(db)

    def create(self, dto: CreateMovimientoDTO) -> MovimientoResponseDTO:
        if dto.tipo == "dividendo":
            raise BadRequestError("Los dividendos se registran mediante /dividendos")

        monto = dto.monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if monto <= 0:
            raise BadRequestError("El monto debe ser al menos 0.01")

        cuenta = self.repo.get_cuenta_for_update(dto.cuenta_id)
        if cuenta is None:
            raise NotFoundError("Cuenta no encontrada")

        saldo = Decimal(str(
            cuenta.saldo_ars if dto.moneda == "ARS" else cuenta.saldo_usd
        ))
        if dto.tipo == "extraccion" and monto > saldo:
            raise BadRequestError("No hay saldo suficiente para realizar la extracción")

        nuevo_saldo = saldo + monto if dto.tipo == "deposito" else saldo - monto
        if dto.moneda == "ARS":
            cuenta.saldo_ars = nuevo_saldo  # type: ignore[assignment]
        else:
            cuenta.saldo_usd = nuevo_saldo  # type: ignore[assignment]

        try:
            movimiento = self.repo.create(
                cuenta_id=dto.cuenta_id,
                tipo=dto.tipo,
                moneda=dto.moneda,
                monto=monto,
                descripcion=dto.descripcion,
            )
        except Exception:
            self.db.rollback()
            raise
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
        if self.repo.find_by_id(movimiento_id) is None:
            return None
        detalle = (
            "Los movimientos contabilizados no se pueden modificar"
            if dto.model_dump(exclude_unset=True)
            else "No se admiten actualizaciones vacías"
        )
        raise ConflictError(detalle)

    def delete(self, movimiento_id: int) -> bool:
        if self.repo.find_by_id(movimiento_id) is None:
            return False
        raise ConflictError("Los movimientos contabilizados no se pueden eliminar")
