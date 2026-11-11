from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Tenencia(Base):
    __tablename__ = "tenencia"

    cuenta_id = Column(Integer, ForeignKey("cuenta.id", ondelete="CASCADE"), primary_key=True)
    activo_id = Column(Integer, ForeignKey("activo.id"), primary_key=True)
    cantidad = Column(Numeric(18, 4), nullable=False)
    precio_promedio = Column(Numeric(15, 4), nullable=False)