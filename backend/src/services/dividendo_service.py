from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models.dividendo_model import Dividendo
from src.db.models.movimiento_model import Movimiento
from src.dtos.dividendo_dto import CreateDividendoDTO, DividendoResponseDTO
from src.mappers.dividendo_mapper import to_dividendo_response
from src.repositories.dividendo_repository import DividendoRepository
from src.utils.errors import BadRequestError, ConflictError, NotFoundError


class DividendoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DividendoRepository(db)

    def registrar_pago(self, dto: CreateDividendoDTO) -> DividendoResponseDTO:
        activo = self.repo.get_activo(dto.activo_id)
        if activo is None:
            raise NotFoundError("Activo no encontrado")

        if activo.tipo not in ("accion", "cedear"):
            raise BadRequestError(
                "Solo se pueden registrar dividendos para acciones o CEDEARs"
            )

        if self.repo.find_by_activo_and_fecha(dto.activo_id, dto.fecha_pago):
            raise ConflictError(
                "Ya existe un dividendo registrado para ese activo y fecha"
            )

        dividendo = Dividendo(
            activo_id=dto.activo_id,
            monto_por_unidad=dto.monto_por_unidad,
            fecha_pago=dto.fecha_pago,
        )
        self.repo.add_dividendo(dividendo)

        try:
            self.repo.flush()
            tenencias = self.repo.list_tenencias(dto.activo_id)
            monto_por_unidad = Decimal(str(dto.monto_por_unidad))

            for tenencia in tenencias:
                monto = (
                    Decimal(str(tenencia.cantidad)) * monto_por_unidad
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if monto <= 0:
                    continue

                cuenta = self.repo.get_cuenta_for_update(tenencia.cuenta_id)
                if cuenta is None:
                    raise NotFoundError(
                        f"No se encontró la cuenta {tenencia.cuenta_id} de una tenencia"
                    )

                if activo.moneda == "ARS":
                    cuenta.saldo_ars = Decimal(str(cuenta.saldo_ars)) + monto
                else:
                    cuenta.saldo_usd = Decimal(str(cuenta.saldo_usd)) + monto

                self.repo.add_movimiento(
                    Movimiento(
                        cuenta_id=cuenta.id,
                        tipo="dividendo",
                        moneda=activo.moneda,
                        monto=monto,
                        descripcion=(
                            f"Pago de dividendo {dividendo.id} "
                            f"del activo {activo.ticker}"
                        ),
                    )
                )

            dividendo = self.repo.commit(dividendo)
        except IntegrityError:
            self.db.rollback()
            if self.repo.find_by_activo_and_fecha(dto.activo_id, dto.fecha_pago):
                raise ConflictError(
                    "Ya existe un dividendo registrado para ese activo y fecha"
                )
            raise

        return to_dividendo_response(dividendo)
