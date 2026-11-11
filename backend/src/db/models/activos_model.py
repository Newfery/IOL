from sqlalchemy import Column, Integer, String, Boolean, Numeric, CheckConstraint
from sqlalchemy.orm import relationship

from src.db.connection import Base
from src.db.models.favoritos_model import Favorito

class Activo(Base):
    __tablename__ = "activo"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(10), nullable=False)
    moneda = Column(String(3), nullable=False)
    precio_actual = Column(Numeric(15, 2), nullable=False)
    nivel_riesgo = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    inversores_favoritos = relationship(
        "Inversor",
        secondary=Favorito.__table__,
        back_populates="favoritos",
    )

    __table_args__ = (
        CheckConstraint("tipo IN ('accion', 'cedear', 'bono')"),
        CheckConstraint("moneda IN ('ARS', 'USD')"),
        CheckConstraint("precio_actual > 0"),
        CheckConstraint("nivel_riesgo BETWEEN 1 AND 5")
    )
