# Importaciones

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from src.db.connection import get_db
from src.dtos.operacion_dto import OperacionCreate, OperacionResponse
from src.mappers.operacion_mapper import OperacionMapper
from src.repositories.operacion_repository import OperacionRepository
from src.services.operacion_service import OperacionService


# Creación del router
router = APIRouter(
    prefix="/operaciones",
    tags=["Operaciones"]
)


# Registrar una nueva operación
@router.post("/", response_model=OperacionResponse)
def crear_operacion(
    dto: OperacionCreate,
    db: Session = Depends(get_db)
):

    # Comprueba qué tipo de operación quiere realizar el usuario
    if dto.tipo == "compra":

        operacion = OperacionService.comprar(
            db=db,
            cuenta_id=dto.cuenta_id,
            activo_id=dto.activo_id,
            cantidad=dto.cantidad
        )

    elif dto.tipo == "venta":

        operacion = OperacionService.vender(
            db=db,
            cuenta_id=dto.cuenta_id,
            activo_id=dto.activo_id,
            cantidad=dto.cantidad
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de operación inválido"
        )

    # Convierte el modelo en un DTO de respuesta
    return OperacionMapper.to_dto(operacion)


# Buscar una operación por su ID
@router.get("/{operacion_id}", response_model=OperacionResponse)
def obtener_operacion(
    operacion_id: int,
    db: Session = Depends(get_db)
):

    # Busca la operación en la base de datos
    operacion = OperacionRepository.obtener_por_id(db, operacion_id)

    # Comprueba si existe
    if operacion is None:
        raise HTTPException(
            status_code=404,
            detail="Operacion no encontrada"
        )

    return OperacionMapper.to_dto(operacion)


# Obtener todas las operaciones de una cuenta
@router.get("/cuenta/{cuenta_id}", response_model=list[OperacionResponse])
def obtener_operaciones_cuenta(
    cuenta_id: int,
    db: Session = Depends(get_db)
):

    # Busca las operaciones de la cuenta
    operaciones = OperacionRepository.obtener_por_cuenta(db, cuenta_id)

    # Convierte la lista de modelos en DTOs
    return OperacionMapper.to_dto_list(operaciones)


# Filtrar operaciones por fecha, tipo y ticker
@router.get("/cuenta/{cuenta_id}/historial")
def filtrar_operaciones(
    cuenta_id: int,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    tipo: Optional[str] = None,
    ticker: Optional[str] = None,
    db: Session = Depends(get_db)
):

    # Busca las operaciones aplicando los filtros
    operaciones = OperacionRepository.filtrar_operaciones(
        db,
        cuenta_id,
        fecha_desde,
        fecha_hasta,
        tipo,
        ticker
    )

    # Calcula las comisiones pagadas en el período
    comisiones = OperacionRepository.obtener_total_comisiones(
        db,
        cuenta_id,
        fecha_desde,
        fecha_hasta
    )

    # Convierte las operaciones en DTOs
    operaciones_dto = OperacionMapper.to_dto_list(operaciones)

    # Devuelve las operaciones y las comisiones
    return {
        "operaciones": operaciones_dto,
        "total_comisiones": comisiones
    }
