from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models.cuenta_model import Cuenta
from src.db.models.inversor_model import Inversor
from src.dtos.movimiento_dto import (
    CreateMovimientoDTO,
    MovimientoResponseDTO,
    UpdateMovimientoDTO,
)
from src.middlewares.auth_middleware import get_current_inversor
from src.schemas.movimiento_schema import (
    CreateMovimientoSchema,
    UpdateMovimientoSchema,
)
from src.services.movimiento_service import MovimientoService

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.post(
    "/",
    response_model=MovimientoResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_movimiento(
    payload: CreateMovimientoSchema,
    db: Session = Depends(get_db),
    current: Inversor = Depends(get_current_inversor),
):
    account_id = db.query(Cuenta.id).filter(
        Cuenta.inversor_id == current.id
    ).scalar()
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    if account_id != payload.cuenta_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )
    dto = CreateMovimientoDTO(**payload.model_dump())
    return MovimientoService(db).create(dto)


@router.get("/", response_model=list[MovimientoResponseDTO])
def list_movimientos(db: Session = Depends(get_db)):
    return MovimientoService(db).list_all()


@router.get("/{movimiento_id}", response_model=MovimientoResponseDTO)
def get_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    result = MovimientoService(db).get_by_id(movimiento_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )
    return result


@router.put("/{movimiento_id}", response_model=MovimientoResponseDTO)
def replace_movimiento(
    movimiento_id: int,
    payload: CreateMovimientoSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateMovimientoDTO(**payload.model_dump())
    result = MovimientoService(db).update(movimiento_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )
    return result


@router.patch("/{movimiento_id}", response_model=MovimientoResponseDTO)
def update_movimiento(
    movimiento_id: int,
    payload: UpdateMovimientoSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateMovimientoDTO(**payload.model_dump(exclude_unset=True))
    result = MovimientoService(db).update(movimiento_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )
    return result


@router.delete(
    "/{movimiento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    deleted = MovimientoService(db).delete(movimiento_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado",
        )
