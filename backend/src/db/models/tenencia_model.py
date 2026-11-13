from sqlalchemy import CheckConstraint, Column, Integer, Numeric, ForeignKey
from src.db.connection import Base


class Tenencia(Base):
    __tablename__ = "tenencia"

    cuenta_id = Column(Integer, ForeignKey("cuenta.id", ondelete="CASCADE"), primary_key=True)
    activo_id = Column(Integer, ForeignKey("activo.id"), primary_key=True)
    cantidad = Column(Numeric(18, 4), nullable=False)
    precio_promedio = Column(Numeric(15, 4), nullable=False)

    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="chk_tenencia_cantidad"),
        CheckConstraint("precio_promedio >= 0", name="chk_tenencia_precio"),
    )