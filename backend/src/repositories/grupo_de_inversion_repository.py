from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.grupo_inversor_model import GrupoInversor
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
        self.db.flush()
        self.db.add(
            GrupoInversor(
                grupo_id=grupo.id,
                inversor_id=creador_id,
                fecha_union=datetime.now(),
            )
        )
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

    def ensure_creator_membership(self, grupo_id: int, creador_id: int) -> None:
        if self.db.get(GrupoInversor, (grupo_id, creador_id)) is None:
            self.db.add(
                GrupoInversor(
                    grupo_id=grupo_id,
                    inversor_id=creador_id,
                    fecha_union=datetime.now(),
                )
            )

    def update(self, grupo: GrupoDeInversion) -> GrupoDeInversion:
        self.db.add(grupo)
        self.db.commit()
        self.db.refresh(grupo)
        return grupo

    def delete(self, grupo: GrupoDeInversion) -> None:
        self.db.query(GrupoInversor).filter(
            GrupoInversor.grupo_id == grupo.id
        ).delete(synchronize_session=False)
        self.db.delete(grupo)
        self.db.commit()
