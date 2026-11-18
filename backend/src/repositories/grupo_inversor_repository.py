from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.grupo_inversor_model import GrupoInversor
from src.db.models.inversor_model import Inversor


class GrupoInversorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        grupo_id: int,
        inversor_id: int,
        fecha_union: datetime,
    ) -> GrupoInversor:
        integrante = GrupoInversor(
            grupo_id=grupo_id,
            inversor_id=inversor_id,
            fecha_union=fecha_union,
        )
        self.db.add(integrante)
        self.db.commit()
        self.db.refresh(integrante)
        return integrante

    def find_by_id(
        self,
        grupo_id: int,
        inversor_id: int,
    ) -> GrupoInversor | None:
        return self.db.get(GrupoInversor, (grupo_id, inversor_id))

    def find_by_grupo(self, grupo_id: int) -> list[GrupoInversor]:
        return (
            self.db.query(GrupoInversor)
            .filter(GrupoInversor.grupo_id == grupo_id)
            .order_by(GrupoInversor.inversor_id)
            .all()
        )

    def group_exists(self, grupo_id: int) -> bool:
        return self.db.get(GrupoDeInversion, grupo_id) is not None

    def find_group(self, grupo_id: int) -> GrupoDeInversion | None:
        return self.db.get(GrupoDeInversion, grupo_id)

    def inversor_exists(self, inversor_id: int) -> bool:
        return self.db.get(Inversor, inversor_id) is not None

    def delete(self, integrante: GrupoInversor) -> None:
        self.db.delete(integrante)
        self.db.commit()
