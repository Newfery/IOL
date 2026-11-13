from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal

from src.db.models.activos_model import Activo
from src.db.models.operacion_model import Operacion


class ActivoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        ticker: str,
        nombre: str,
        tipo: str,
        moneda: str,
        precio_actual: Decimal,
        nivel_riesgo: int,
        activo: bool = True
    ) -> Activo:

        nuevo_activo = Activo(
            ticker=ticker,
            nombre=nombre,
            tipo=tipo,
            moneda=moneda,
            precio_actual=precio_actual,
            nivel_riesgo=nivel_riesgo,
            activo=activo
        )

        self.db.add(nuevo_activo)
        self.db.commit()
        self.db.refresh(nuevo_activo)

        return nuevo_activo

    def get_by_id(self, activo_id: int) -> Activo | None:
        return self.db.query(Activo).filter(
            Activo.id == activo_id
        ).first()

    def get_by_ticker(self, ticker: str) -> Activo | None:
        return self.db.query(Activo).filter(
            Activo.ticker == ticker
        ).first()

    def get_all(
        self,
        tipo: str | None = None,
        moneda: str | None = None
    ) -> list[Activo]:

        query = self.db.query(Activo)

        if tipo is not None:
            query = query.filter(Activo.tipo == tipo)

        if moneda is not None:
            query = query.filter(Activo.moneda == moneda)

        return query.all()

    def get_mas_operados(self, dias: int = 7, limite: int = 10) -> list[tuple[Activo, object]]:
        desde = datetime.now() - timedelta(days=dias)
        return (
            self.db.query(
                Activo,
                func.coalesce(func.sum(Operacion.cantidad), 0).label("volumen"),
            )
            .join(Operacion, Operacion.activo_id == Activo.id)
            .filter(
                Operacion.fecha >= desde,
                Operacion.estado == "ejecutada",
            )
            .group_by(Activo.id)
            .order_by(func.sum(Operacion.cantidad).desc(), Activo.ticker)
            .limit(limite)
            .all()
        )

    def update(self, activo: Activo) -> Activo:
        self.db.add(activo)
        self.db.commit()
        self.db.refresh(activo)

        return activo

    def delete(self, activo: Activo) -> None:
        self.db.delete(activo)
        self.db.commit()