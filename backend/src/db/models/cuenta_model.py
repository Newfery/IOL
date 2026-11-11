from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)

from src.db.connection import Base


class Cuenta(Base):
    __tablename__ = "cuenta"

    id = Column(Integer, primary_key=True)
    inversor_id = Column(
        Integer,
        ForeignKey("inversor.id", ondelete="CASCADE", name="fk_cuenta_inversor"),
        unique=True,
        nullable=False,
    )
    numero_comitente = Column(String(50), unique=True, nullable=False)
    saldo_ars = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        server_default=text("0.00"),
    )
    saldo_usd = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        server_default=text("0.00"),
    )

    __table_args__ = (
        CheckConstraint("saldo_ars >= 0", name="chk_saldo_ars"),
        CheckConstraint("saldo_usd >= 0", name="chk_saldo_usd"),
    )
    