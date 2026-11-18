from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.grupo_inversor_dto import (
    CreateGrupoInversorDTO,
    GrupoInversorResponseDTO,
)
from src.schemas.grupo_inversor_schema import CreateGrupoInversorSchema
from src.services.grupo_inversor_service import GrupoInversorService

router = APIRouter(
    prefix="/grupos-inversion/{grupo_id}/integrantes",
    tags=["integrantes de grupos de inversión"],
)


@router.post(
    "/",
    response_model=GrupoInversorResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_integrante(
    grupo_id: int,
    payload: CreateGrupoInversorSchema,
    db: Session = Depends(get_db),
):
    dto = CreateGrupoInversorDTO(
        grupo_id=grupo_id,
        **payload.model_dump(),
    )
    return GrupoInversorService(db).create(dto)


@router.get("/", response_model=list[GrupoInversorResponseDTO])
def list_integrantes(grupo_id: int, db: Session = Depends(get_db)):
    return GrupoInversorService(db).get_by_grupo(grupo_id)


@router.get("/{inversor_id}", response_model=GrupoInversorResponseDTO)
def get_integrante(
    grupo_id: int,
    inversor_id: int,
    db: Session = Depends(get_db),
):
    result = GrupoInversorService(db).get_by_id(grupo_id, inversor_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El inversor no pertenece al grupo",
        )
    return result


@router.delete(
    "/{inversor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_integrante(
    grupo_id: int,
    inversor_id: int,
    db: Session = Depends(get_db),
):
    if not GrupoInversorService(db).delete(grupo_id, inversor_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El inversor no pertenece al grupo",
        )
