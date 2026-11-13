from decimal import Decimal

from sqlalchemy.orm import Session

from src.db.models.activos_model import Activo
from src.db.models.cuenta_model import Cuenta
from src.db.models.operacion_model import Operacion
from src.db.models.tenencia_model import Tenencia


class CuentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        inversor_id: int,
        numero_comitente: str,
        saldo_ars: Decimal = Decimal("0.00"),
        saldo_usd: Decimal = Decimal("0.00"),
    ) -> Cuenta:
        cuenta = Cuenta(
            inversor_id=inversor_id,
            numero_comitente=numero_comitente,
            saldo_ars=saldo_ars,
            saldo_usd=saldo_usd,
        )
        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def find_by_id(self, cuenta_id: int) -> Cuenta | None:
        return self.db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()

    def list_all(self) -> list[Cuenta]:
        return self.db.query(Cuenta).all()

    def list_tenencias(self, cuenta_id: int) -> list[tuple[Tenencia, Activo]]:
        return (
            self.db.query(Tenencia, Activo)
            .join(Activo, Activo.id == Tenencia.activo_id)
            .filter(Tenencia.cuenta_id == cuenta_id)
            .order_by(Activo.ticker)
            .all()
        )

    def realized_gains_by_year(self, cuenta_id: int) -> list[tuple[int, object]]:
        from sqlalchemy import extract, func

        return (
            self.db.query(
                extract("year", Operacion.fecha).label("anio"),
                func.coalesce(func.sum(Operacion.resultado_realizado), 0),
            )
            .filter(
                Operacion.cuenta_id == cuenta_id,
                Operacion.tipo == "venta",
                Operacion.estado == "ejecutada",
            )
            .group_by(extract("year", Operacion.fecha))
            .order_by(extract("year", Operacion.fecha))
            .all()
        )

    def update(self, cuenta_id: int, **fields: object) -> Cuenta | None:
        cuenta = self.find_by_id(cuenta_id)
        if cuenta is None:
            return None

        allowed_fields = {
            "inversor_id",
            "numero_comitente",
            "saldo_ars",
            "saldo_usd",
        }
        invalid_fields = fields.keys() - allowed_fields
        if invalid_fields:
            raise ValueError(f"Campos no actualizables para Cuenta: {', '.join(sorted(invalid_fields))}")

        for field, value in fields.items():
            setattr(cuenta, field, value)

        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def delete(self, cuenta_id: int) -> bool:
        cuenta = self.find_by_id(cuenta_id)
        if cuenta is None:
            return False

        self.db.delete(cuenta)
        self.db.commit()
        return True
