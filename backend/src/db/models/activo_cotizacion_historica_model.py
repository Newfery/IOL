from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, UniqueConstraint

from src.db.connection import Base


class ActivoCotizacionHistorica(Base):
    __tablename__ = "activo_cotizacion_historica"

    id = Column(Integer, primary_key=True)
    activo_id = Column(Integer, ForeignKey("activo.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, nullable=False)
    precio = Column(Numeric(15, 6), nullable=False)

    __table_args__ = (
        UniqueConstraint("activo_id", "fecha", name="uq_activo_cotizacion_historica_activo_fecha"),
        CheckConstraint("precio > 0", name="chk_activo_cotizacion_historica_precio"),
    )
