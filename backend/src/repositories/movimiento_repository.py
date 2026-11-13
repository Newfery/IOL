from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from src.db.models.cuenta_model import Cuenta
from src.db.models.movimiento_model import Movimiento


class MovimientoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        cuenta_id: int,
        tipo: Literal["deposito", "extraccion", "dividendo"],
        moneda: Literal["ARS", "USD"],
        monto: Decimal,
        descripcion: str | None = None,
    ) -> Movimiento:
        movimiento = Movimiento(
            cuenta_id=cuenta_id,
            tipo=tipo,
            moneda=moneda,
            monto=monto,
            descripcion=descripcion,
        )
        self.db.add(movimiento)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def get_cuenta_for_update(self, cuenta_id: int) -> Cuenta | None:
        return (
            self.db.query(Cuenta)
            .filter(Cuenta.id == cuenta_id)
            .with_for_update()
            .first()
        )

    def find_by_id(self, movimiento_id: int) -> Movimiento | None:
        return (
            self.db.query(Movimiento)
            .filter(Movimiento.id == movimiento_id)
            .first()
        )

    def list_all(self) -> list[Movimiento]:
        return self.db.query(Movimiento).all()

    def update(self, movimiento_id: int, **fields: object) -> Movimiento | None:
        movimiento = self.find_by_id(movimiento_id)
        if movimiento is None:
            return None

        allowed_fields = {
            "cuenta_id",
            "tipo",
            "moneda",
            "monto",
            "descripcion",
        }
        invalid_fields = fields.keys() - allowed_fields
        if invalid_fields:
            raise ValueError(
                f"Campos no actualizables para Movimiento: {', '.join(sorted(invalid_fields))}"
            )

        for field, value in fields.items():
            setattr(movimiento, field, value)

        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def delete(self, movimiento_id: int) -> bool:
        movimiento = self.find_by_id(movimiento_id)
        if movimiento is None:
            return False

        self.db.delete(movimiento)
        self.db.commit()
        return True
