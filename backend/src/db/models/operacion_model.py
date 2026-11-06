from sqlalchemy import Column, Integer, String

from src.db.connection import Base


class Operacion(Base):
    __tablename__ = "operaciones"

    id = Column(Integer, primary_key=True)
    cuenta_id = Column(String, nullable=False)
    activo_id = Column(Integer, unique=True, nullable=False)
    tipo = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Integer, nullable=False)
    comision = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    fecha = Column(String, nullable=False)
    estado = Column(String, nullable=False)