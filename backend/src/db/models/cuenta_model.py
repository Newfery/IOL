from sqlalchemy import Column, Integer, String

from src.db.connection import Base


class Cuenta(Base):
    __tablename__ = "Cuentas"

    id = Column(Integer, primary_key=True)
    inversor_id = Column(String, nullable=False)
    numero_comitente = Column(Integer, unique=True, nullable=False)
    saldo_ars = Column(Integer, nullable=False)
    saldo_usd = Column(Integer, nullable=False)

    