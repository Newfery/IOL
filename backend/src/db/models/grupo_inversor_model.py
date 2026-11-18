from sqlalchemy import Column, DateTime, ForeignKey, Integer, text

from src.db.connection import Base


class GrupoInversor(Base):
    __tablename__ = "grupo_inversor"

    grupo_id = Column(
        Integer,
        ForeignKey(
            "grupo_de_inversion.id",
            name="fk_grupo_inversor_grupo",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    inversor_id = Column(
        Integer,
        ForeignKey(
            "inversor.id",
            name="fk_grupo_inversor_inversor",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    fecha_union = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
