from sqlalchemy.orm import Session
from decimal import Decimal

from src.db.models.tenencia_grupo_model import TenenciaGrupo


class TenenciaGrupoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, grupo_id: int, activo_id: int, cantidad: Decimal, precio_promedio: Decimal) -> TenenciaGrupo:
        tenencia_grupo = TenenciaGrupo(
            grupo_id=grupo_id,
            activo_id=activo_id,
            cantidad=cantidad,
            precio_promedio=precio_promedio
        )
        self.db.add(tenencia_grupo)
        self.db.commit()
        self.db.refresh(tenencia_grupo)
        return tenencia_grupo

    def get_by_id(self, grupo_id: int, activo_id: int) -> TenenciaGrupo | None:
        return self.db.query(TenenciaGrupo).filter(
            TenenciaGrupo.grupo_id == grupo_id,
            TenenciaGrupo.activo_id == activo_id
        ).first()

    def update(self, tenencia_grupo: TenenciaGrupo) -> TenenciaGrupo:
        self.db.add(tenencia_grupo)
        self.db.commit()
        self.db.refresh(tenencia_grupo)
        return tenencia_grupo

    def delete(self, tenencia_grupo: TenenciaGrupo) -> None:
        self.db.delete(tenencia_grupo)
        self.db.commit()