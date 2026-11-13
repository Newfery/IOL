from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models.activos_model import Activo
from src.db.models.cuenta_model import Cuenta
from src.db.models.dividendo_model import Dividendo
from src.db.models.movimiento_model import Movimiento
from src.db.models.tenencia_model import Tenencia


class DividendoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activo(self, activo_id: int) -> Activo | None:
        return self.db.query(Activo).filter(Activo.id == activo_id).first()

    def find_by_activo_and_fecha(
        self,
        activo_id: int,
        fecha_pago: datetime,
    ) -> Dividendo | None:
        return (
            self.db.query(Dividendo)
            .filter(
                Dividendo.activo_id == activo_id,
                Dividendo.fecha_pago == fecha_pago,
            )
            .first()
        )

    def list_tenencias(self, activo_id: int) -> list[Tenencia]:
        return (
            self.db.query(Tenencia)
            .filter(Tenencia.activo_id == activo_id, Tenencia.cantidad > 0)
            .with_for_update()
            .all()
        )

    def get_cuenta_for_update(self, cuenta_id: int) -> Cuenta | None:
        return (
            self.db.query(Cuenta)
            .filter(Cuenta.id == cuenta_id)
            .with_for_update()
            .first()
        )

    def add_dividendo(self, dividendo: Dividendo) -> None:
        self.db.add(dividendo)

    def add_movimiento(self, movimiento: Movimiento) -> None:
        self.db.add(movimiento)

    def flush(self) -> None:
        self.db.flush()

    def commit(self, dividendo: Dividendo) -> Dividendo:
        self.db.commit()
        self.db.refresh(dividendo)
        return dividendo
