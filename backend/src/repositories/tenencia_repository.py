from sqlalchemy.orm import Session

from src.db.models.tenencia_model import Tenencia


class TenenciaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, cuenta_id: int, activo_id: int, cantidad: float, precio_promedio: float) -> Tenencia:
        tenencia = Tenencia(
            cuenta_id=cuenta_id,
            activo_id=activo_id,
            cantidad=cantidad,
            precio_promedio=precio_promedio
        )
        self.db.add(tenencia)
        self.db.commit()
        self.db.refresh(tenencia)
        return tenencia

    def get_by_id(self, cuenta_id: int, activo_id: int) -> Tenencia | None:
        return self.db.query(Tenencia).filter(
            Tenencia.cuenta_id == cuenta_id,
            Tenencia.activo_id == activo_id
        ).first()

    def update(self, tenencia: Tenencia) -> Tenencia:
        self.db.add(tenencia)
        self.db.commit()
        self.db.refresh(tenencia)
        return tenencia

    def delete(self, tenencia: Tenencia) -> None:
        self.db.delete(tenencia)
        self.db.commit()