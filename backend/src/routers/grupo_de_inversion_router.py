from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.grupo_de_inversion_dto import (
    CreateGrupoDeInversionDTO,
    GrupoDeInversionResponseDTO,
    UpdateGrupoDeInversionDTO,
)
from src.schemas.grupo_de_inversion_schema import (
    CreateGrupoDeInversionSchema,
    UpdateGrupoDeInversionSchema,
)
from src.services.grupo_de_inversion_service import GrupoDeInversionService

router = APIRouter(prefix="/grupos-inversion", tags=["grupos de inversión"])


@router.post(
    "/",
    response_model=GrupoDeInversionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_grupo(
    payload: CreateGrupoDeInversionSchema,
    db: Session = Depends(get_db),
):
    dto = CreateGrupoDeInversionDTO(**payload.model_dump())
    return GrupoDeInversionService(db).create(dto)


@router.get("/", response_model=list[GrupoDeInversionResponseDTO])
def list_grupos(db: Session = Depends(get_db)):
    return GrupoDeInversionService(db).list_all()


@router.get("/{grupo_id}", response_model=GrupoDeInversionResponseDTO)
def get_grupo(grupo_id: int, db: Session = Depends(get_db)):
    result = GrupoDeInversionService(db).get_by_id(grupo_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de inversión no encontrado",
        )
    return result


@router.put("/{grupo_id}", response_model=GrupoDeInversionResponseDTO)
def replace_grupo(
    grupo_id: int,
    payload: CreateGrupoDeInversionSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateGrupoDeInversionDTO(**payload.model_dump())
    result = GrupoDeInversionService(db).update(grupo_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de inversión no encontrado",
        )
    return result


@router.patch("/{grupo_id}", response_model=GrupoDeInversionResponseDTO)
def update_grupo(
    grupo_id: int,
    payload: UpdateGrupoDeInversionSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateGrupoDeInversionDTO(**payload.model_dump(exclude_unset=True))
    result = GrupoDeInversionService(db).update(grupo_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de inversión no encontrado",
        )
    return result


@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grupo(grupo_id: int, db: Session = Depends(get_db)):
    if not GrupoDeInversionService(db).delete(grupo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de inversión no encontrado",
        )
