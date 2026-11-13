from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models.activos_model import Activo
from src.db.models.favoritos_model import Favorito
from src.db.models.inversor_model import Inversor


class FavoritosRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, inversor_id: int, activo_id: int) -> Favorito:
        favorito = Favorito(inversor_id=inversor_id, activo_id=activo_id)
        self.db.add(favorito)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(favorito)
        return favorito

    def get_by_id(self, inversor_id: int, activo_id: int) -> Favorito | None:
        return self.db.get(Favorito, (inversor_id, activo_id))

    def get_by_inversor(self, inversor_id: int) -> list[Favorito]:
        return (
            self.db.query(Favorito)
            .filter(Favorito.inversor_id == inversor_id)
            .order_by(Favorito.activo_id)
            .all()
        )

    def inversor_exists(self, inversor_id: int) -> bool:
        return self.db.get(Inversor, inversor_id) is not None

    def activo_exists(self, activo_id: int) -> bool:
        return self.db.get(Activo, activo_id) is not None

    def delete(self, favorito: Favorito) -> None:
        self.db.delete(favorito)
        self.db.commit()

    def get_mas_favoritos(self, limite: int = 10) -> list[tuple[Activo, int]]:
        return (
            self.db.query(Activo, func.count(Favorito.inversor_id).label("cantidad"))
            .join(Favorito, Favorito.activo_id == Activo.id)
            .group_by(Activo.id)
            .order_by(func.count(Favorito.inversor_id).desc(), Activo.ticker)
            .limit(limite)
            .all()
        )
