from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, text

from src.db.connection import Base


class AporteGrupo(Base):
    __tablename__ = "aporte_grupo"

    id = Column(Integer, primary_key=True)
    grupo_id = Column(Integer, ForeignKey("grupo_de_inversion.id", ondelete="CASCADE"), nullable=False)
    inversor_id = Column(Integer, ForeignKey("inversor.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    fecha = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
