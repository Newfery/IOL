from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

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

    # Relaciones
    cuenta = relationship("Cuenta", back_populates="operaciones")
    activo = relationship("Activo", back_populates="operaciones")

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
    )