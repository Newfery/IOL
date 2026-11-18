from sqlalchemy.orm import Session

from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.inversor_model import Inversor


class GrupoDeInversionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        nombre: str,
        codigo_union: str,
        creador_id: int,
        plata_disponible,
    ) -> GrupoDeInversion:
        grupo = GrupoDeInversion(
            nombre=nombre,
            codigo_union=codigo_union,
            creador_id=creador_id,
            plata_disponible=plata_disponible,
        )
        self.db.add(grupo)
        self.db.commit()
        self.db.refresh(grupo)
        return grupo

    def find_by_id(self, grupo_id: int) -> GrupoDeInversion | None:
        return self.db.get(GrupoDeInversion, grupo_id)

    def find_by_nombre(self, nombre: str) -> GrupoDeInversion | None:
        return (
            self.db.query(GrupoDeInversion)
            .filter(GrupoDeInversion.nombre == nombre)
            .first()
        )

    def find_by_codigo_union(self, codigo_union: str) -> GrupoDeInversion | None:
        return (
            self.db.query(GrupoDeInversion)
            .filter(GrupoDeInversion.codigo_union == codigo_union)
            .first()
        )

    def list_all(self) -> list[GrupoDeInversion]:
        return (
            self.db.query(GrupoDeInversion)
            .order_by(GrupoDeInversion.id)
            .all()
        )

    def inversor_exists(self, inversor_id: int) -> bool:
        return self.db.get(Inversor, inversor_id) is not None

    def update(self, grupo: GrupoDeInversion) -> GrupoDeInversion:
        self.db.add(grupo)
        self.db.commit()
        self.db.refresh(grupo)
        return grupo

    def delete(self, grupo: GrupoDeInversion) -> None:
        self.db.delete(grupo)
        self.db.commit()
