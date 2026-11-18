from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.db.connection import Base

class Operacion(Base):
    __tablename__ = "operacion"

    id = Column(Integer, primary_key=True, index=True)
    cuenta_id = Column(Integer, ForeignKey("cuenta.id"), nullable=False)
    activo_id = Column(Integer, ForeignKey("activo.id"), nullable=False)
    tipo = Column(String(20), nullable=False)
    cantidad = Column(DECIMAL(18, 4), nullable=False)
    precio_unitario = Column(DECIMAL(15, 4), nullable=False)
    comision = Column(DECIMAL(15, 2), nullable=False)
    total = Column(DECIMAL(15, 2), nullable=False)
    resultado_realizado = Column(DECIMAL(15, 2), nullable=True)
    fecha = Column(DateTime, server_default=func.now())
    estado = Column(String(20), nullable=False)
    liquidacion_dias = Column(Integer, nullable=False, default=0, server_default="0")
    liquidacion_acreditada = Column(Boolean, nullable=False, default=True, server_default="true")
    fecha_liquidacion = Column(DateTime, nullable=True)

    cuenta = relationship("Cuenta")
    activo = relationship("Activo")

    # Restricciones
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('compra', 'venta')",
            name="chk_operacion_tipo"
        ),
        CheckConstraint(
            "cantidad > 0",
            name="chk_operacion_cantidad"
        ),
        CheckConstraint(
            "precio_unitario > 0",
            name="chk_operacion_precio"
        ),
        CheckConstraint(
            "comision >= 0",
            name="chk_operacion_comision"
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'ejecutada', 'rechazada')",
            name="chk_operacion_estado"
        ),
        CheckConstraint("liquidacion_dias BETWEEN 0 AND 2", name="chk_operacion_liquidacion_dias"),
    )
