from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, text

from src.db.connection import Base


class GrupoDeInversion(Base):
    __tablename__ = "grupo_de_inversion"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), unique=True, nullable=False)
    codigo_union = Column(String(50), unique=True, nullable=False)
    creador_id = Column(
        Integer,
        ForeignKey("inversor.id", name="fk_grupo_creador"),
        nullable=False,
    )
    password_hash = Column(String(255), nullable=True)
    plata_disponible = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        server_default=text("0.00"),
    )
    fecha_creacion = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint("plata_disponible >= 0", name="chk_grupo_plata"),
    )
