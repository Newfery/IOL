from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from src.db.connection import Base


class Movimiento(Base):
    __tablename__ = "movimiento"

    id = Column(Integer, primary_key=True)
    cuenta_id = Column(Integer, ForeignKey("cuenta.id"), nullable=False)
    tipo = Column(String(20), nullable=False)
    moneda = Column(String(3), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    fecha = Column(DateTime, server_default=func.now())
    descripcion = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("monto > 0", name="chk_movimiento_monto"),
        CheckConstraint(
            "tipo IN ('deposito', 'extraccion', 'dividendo')",
            name="chk_movimiento_tipo",
        ),
        CheckConstraint(
            "moneda IN ('ARS', 'USD')",
            name="chk_movimiento_moneda",
        ),
    )
