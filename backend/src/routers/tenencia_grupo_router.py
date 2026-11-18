from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.tenencia_grupo_dto import CreateTenenciaGrupoDTO, UpdateTenenciaGrupoDTO, TenenciaGrupoResponseDTO
from src.schemas.tenencia_grupo_schema import CreateTenenciaGrupoSchema, UpdateTenenciaGrupoSchema
from src.services.tenencia_grupo_service import TenenciaGrupoService

router = APIRouter(prefix="/tenencias-grupo", tags=["tenencias-grupo"])


@router.post("/", response_model=TenenciaGrupoResponseDTO, status_code=status.HTTP_201_CREATED)
def create_tenencia_grupo(payload: CreateTenenciaGrupoSchema, db: Session = Depends(get_db)):
    """Valida con Schema, arma DTO y llama al service."""
    dto = CreateTenenciaGrupoDTO(**payload.model_dump())
    return TenenciaGrupoService(db).create(dto)


@router.get("/{grupo_id}/{activo_id}", response_model=TenenciaGrupoResponseDTO)
def get_tenencia_grupo(grupo_id: int, activo_id: int, db: Session = Depends(get_db)):
    result = TenenciaGrupoService(db).get_by_id(grupo_id, activo_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia de grupo no encontrada"
        )

    return result


@router.put("/{grupo_id}/{activo_id}", response_model=TenenciaGrupoResponseDTO)
def update_tenencia_grupo(grupo_id: int, activo_id: int, payload: CreateTenenciaGrupoSchema, db: Session = Depends(get_db)):
    dto = UpdateTenenciaGrupoDTO(
        **payload.model_dump(exclude={"grupo_id", "activo_id"})
    )

    result = TenenciaGrupoService(db).update(grupo_id, activo_id, dto)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia de grupo no encontrada"
        )

    return result


@router.patch("/{grupo_id}/{activo_id}", response_model=TenenciaGrupoResponseDTO)
def patch_tenencia_grupo(grupo_id: int, activo_id: int, payload: UpdateTenenciaGrupoSchema, db: Session = Depends(get_db)):
    dto = UpdateTenenciaGrupoDTO(**payload.model_dump(exclude_unset=True))

    result = TenenciaGrupoService(db).update(grupo_id, activo_id, dto)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia de grupo no encontrada"
        )

    return result


@router.delete("/{grupo_id}/{activo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenencia_grupo(grupo_id: int, activo_id: int, db: Session = Depends(get_db)):
    deleted = TenenciaGrupoService(db).delete(grupo_id, activo_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia de grupo no encontrada"
        )