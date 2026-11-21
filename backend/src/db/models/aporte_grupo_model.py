from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)

from src.db.connection import Base


class AporteGrupo(Base):
    __tablename__ = "aporte_grupo"

    id = Column(Integer, primary_key=True)
    grupo_id = Column(Integer, ForeignKey("grupo_de_inversion.id", ondelete="CASCADE"), nullable=False)
    inversor_id = Column(Integer, ForeignKey("inversor.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    moneda = Column(String(3), nullable=False, server_default=text("'ARS'"))
    monto_original = Column(Numeric(15, 2), nullable=False)
    cotizacion_mep = Column(Numeric(15, 4))
    fecha = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        CheckConstraint("moneda IN ('ARS', 'USD')", name="chk_aporte_grupo_moneda"),
        CheckConstraint("monto_original > 0", name="chk_aporte_grupo_monto_original"),
        CheckConstraint(
            "(moneda = 'ARS' AND cotizacion_mep IS NULL) OR "
            "(moneda = 'USD' AND cotizacion_mep > 0)",
            name="chk_aporte_grupo_cotizacion_mep",
        ),
    )
