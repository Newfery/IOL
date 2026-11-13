from uuid import uuid4

from sqlalchemy.orm import Session

from src.db.models.cuenta_model import Cuenta
from src.db.models.inversor_model import Inversor


class InversorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, nombre: str, email: str, cuit: str, perfil_riesgo: str) -> Inversor:
        inversor = Inversor(
            nombre=nombre,
            email=email,
            cuit=cuit,
            perfil_riesgo=perfil_riesgo
        )
        self.db.add(inversor)
        self.db.flush()
        self.db.add(
            Cuenta(
                inversor_id=inversor.id,
                numero_comitente=f"COM-{uuid4().hex.upper()}",
                saldo_ars=0,
                saldo_usd=0,
            )
        )
        self.db.commit()
        self.db.refresh(inversor)
        return inversor

    def get_by_id(self, inversor_id: int) -> Inversor | None:
        return self.db.query(Inversor).filter(Inversor.id == inversor_id).first()

    def get_by_email(self, email: str) -> Inversor | None:
        return self.db.query(Inversor).filter(Inversor.email == email).first()

    def get_by_cuit(self, cuit: str) -> Inversor | None:
        return self.db.query(Inversor).filter(Inversor.cuit == cuit).first()

    def update(self, inversor: Inversor) -> Inversor:
        self.db.add(inversor)
        self.db.commit()
        self.db.refresh(inversor)
        return inversor

    def delete(self, inversor: Inversor) -> None:
        self.db.delete(inversor)
        self.db.commit()