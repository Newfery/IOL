from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, Integer, String

from src.db.connection import Base


class Inversor(Base):
    __tablename__ = "inversor"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    cuit = Column(String(11), unique=True, nullable=False)
    perfil_riesgo = Column(String, nullable=False)
    fecha_alta = Column(Date, default=date.today)

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