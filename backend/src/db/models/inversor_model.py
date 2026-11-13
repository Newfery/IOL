from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from src.db.connection import Base
from src.db.models.activos_model import Activo
from src.db.models.favoritos_model import Favorito


class Inversor(Base):
    __tablename__ = "inversor"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    cuit = Column(String(11), unique=True, nullable=False)
    perfil_riesgo = Column(String, nullable=False)
    fecha_alta = Column(Date, default=date.today)
    favoritos = relationship(
        Activo,
        secondary=Favorito.__table__,
        back_populates="inversores_favoritos",
    )

    __table_args__ = (
        CheckConstraint(
            "length(cuit) = 11 AND cuit NOT GLOB '*[^0-9]*'"
        ),
        CheckConstraint(
            "perfil_riesgo IN ('conservador', 'moderado', 'agresivo')"
        ),
    )

    def __repr__(self):
        return f"Inversor(nombre={self.nombre}, email={self.email})"