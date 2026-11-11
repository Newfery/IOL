# Importaciones
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.models.operacion_model import Operacion
from src.db.models.activos_model import Activo


class OperacionRepository:

    # Guarda una nueva operación en la base de datos
    @staticmethod
    def crear(db: Session, operacion: Operacion):

        db.add(operacion)
        db.commit()
        db.refresh(operacion)

        return operacion

    # Busca una operación por su ID
    @staticmethod
    def obtener_por_id(db: Session, operacion_id: int):

        return db.query(Operacion).filter(
            Operacion.id == operacion_id
        ).first()

    # Obtiene todas las operaciones de una cuenta
    @staticmethod
    def obtener_por_cuenta(db: Session, cuenta_id: int):

        return db.query(Operacion).filter(
            Operacion.cuenta_id == cuenta_id
        ).order_by(Operacion.fecha.desc()).all()

    # Obtiene operaciones aplicando filtros
    @staticmethod
    def filtrar_operaciones(
        db: Session,
        cuenta_id: int,
        fecha_desde=None,
        fecha_hasta=None,
        tipo=None,
        ticker=None
    ):

        consulta = db.query(Operacion).filter(
            Operacion.cuenta_id == cuenta_id
        )

        # Filtra por fecha inicial
        if fecha_desde:
            consulta = consulta.filter(
                Operacion.fecha >= fecha_desde
            )

        # Filtra por fecha final
        if fecha_hasta:
            consulta = consulta.filter(
                Operacion.fecha <= fecha_hasta
            )

        # Filtra por tipo de operación
        if tipo:
            consulta = consulta.filter(
                Operacion.tipo == tipo
            )

        # Filtra por ticker del activo
        if ticker:
            consulta = consulta.join(Activo).filter(
                Activo.ticker == ticker
            )

        # Ordena las operaciones desde la más reciente
        return consulta.order_by(
            Operacion.fecha.desc()
        ).all()

    # Calcula el total de comisiones pagadas
    @staticmethod
    def obtener_total_comisiones(
        db: Session,
        cuenta_id: int,
        fecha_desde=None,
        fecha_hasta=None
    ):

        consulta = db.query(
            func.coalesce(func.sum(Operacion.comision), 0)
        ).filter(
            Operacion.cuenta_id == cuenta_id,
            Operacion.estado == "ejecutada"
        )

        if fecha_desde:
            consulta = consulta.filter(
                Operacion.fecha >= fecha_desde
            )

        if fecha_hasta:
            consulta = consulta.filter(
                Operacion.fecha <= fecha_hasta
            )

        return consulta.scalar()