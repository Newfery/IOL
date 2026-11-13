from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)

from src.db.connection import Base


class Dividendo(Base):
    __tablename__ = "dividendo"

    id = Column(Integer, primary_key=True)
    activo_id = Column(Integer, ForeignKey("activo.id"), nullable=False)
    monto_por_unidad = Column(Numeric(15, 4), nullable=False)
    fecha_pago = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "monto_por_unidad > 0",
            name="chk_dividendo_monto",
        ),
        UniqueConstraint(
            "activo_id",
            "fecha_pago",
            name="uq_dividendo_activo_fecha_pago",
        ),
    )