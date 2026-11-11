from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.activo_dto import (
    CreateActivoDTO,
    UpdateActivoDTO,
    ActivoResponseDTO
)
from src.schemas.activos_schema import (
    CreateActivoSchema,
    UpdateActivoSchema
)
from src.services.activos_service import ActivoService


router = APIRouter(prefix="/activos", tags=["activos"])


@router.post("/", response_model=ActivoResponseDTO, status_code=status.HTTP_201_CREATED)
def create_activo(payload: CreateActivoSchema, db: Session = Depends(get_db)):
    dto = CreateActivoDTO(**payload.model_dump())
    return ActivoService(db).create(dto)


@router.get("/", response_model=list[ActivoResponseDTO])
def get_activos(
    tipo: Literal["accion", "cedear", "bono"] | None = None,
    moneda: Literal["ARS", "USD"] | None = None,
    db: Session = Depends(get_db)
):
    return ActivoService(db).get_all(tipo=tipo, moneda=moneda)


@router.get("/{activo_id}", response_model=ActivoResponseDTO)
def get_activo(activo_id: int, db: Session = Depends(get_db)):
    result = ActivoService(db).get_by_id(activo_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado"
        )

    return result


@router.put("/{activo_id}", response_model=ActivoResponseDTO)
def update_activo(
    activo_id: int,
    payload: CreateActivoSchema,
    db: Session = Depends(get_db)
):
    dto = UpdateActivoDTO(**payload.model_dump())
    result = ActivoService(db).update(activo_id, dto)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado"
        )

    return result


@router.patch("/{activo_id}", response_model=ActivoResponseDTO)
def patch_activo(
    activo_id: int,
    payload: UpdateActivoSchema,
    db: Session = Depends(get_db)
):
    dto = UpdateActivoDTO(**payload.model_dump(exclude_unset=True))
    result = ActivoService(db).update(activo_id, dto)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado"
        )

    return result


@router.delete("/{activo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activo(activo_id: int, db: Session = Depends(get_db)):
    deleted = ActivoService(db).delete(activo_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado"
        )