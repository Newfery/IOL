from sqlalchemy.orm import Session

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
        self.db.commit()
        self.db.refresh(inversor)
        return inversor

    def get_by_id(self, inversor_id: int) -> Inversor | None:
        return self.db.query(Inversor).filter(Inversor.id == inversor_id).first()

    def update(self, inversor: Inversor) -> Inversor:
        self.db.add(inversor)
        self.db.commit()
        self.db.refresh(inversor)
        return inversor

    def delete(self, inversor: Inversor) -> None:
        self.db.delete(inversor)
        self.db.commit()