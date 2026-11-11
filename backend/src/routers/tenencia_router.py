from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.tenencia_dto import CreateTenenciaDTO, UpdateTenenciaDTO, TenenciaResponseDTO
from src.schemas.tenencia_schema import CreateTenenciaSchema, UpdateTenenciaSchema
from src.services.tenencia_service import TenenciaService

router = APIRouter(prefix="/tenencias", tags=["tenencias"])


@router.post("/", response_model=TenenciaResponseDTO, status_code=status.HTTP_201_CREATED)
def create_tenencia(payload: CreateTenenciaSchema, db: Session = Depends(get_db)):
    """Valida con Schema, arma DTO y llama al service."""
    dto = CreateTenenciaDTO(**payload.model_dump())
    return TenenciaService(db).create(dto)


@router.get("/{cuenta_id}/{activo_id}", response_model=TenenciaResponseDTO)
def get_tenencia(cuenta_id: int, activo_id: int, db: Session = Depends(get_db)):
    result = TenenciaService(db).get_by_id(cuenta_id, activo_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia no encontrada"
        )
    return result


@router.put("/{cuenta_id}/{activo_id}", response_model=TenenciaResponseDTO)
def update_tenencia(cuenta_id: int, activo_id: int, payload: CreateTenenciaSchema, db: Session = Depends(get_db)):
    dto = UpdateTenenciaDTO(**payload.model_dump(exclude={"cuenta_id", "activo_id"}))
    result = TenenciaService(db).update(cuenta_id, activo_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia no encontrada"
        )
    return result


@router.patch("/{cuenta_id}/{activo_id}", response_model=TenenciaResponseDTO)
def patch_tenencia(cuenta_id: int, activo_id: int, payload: UpdateTenenciaSchema, db: Session = Depends(get_db)):
    dto = UpdateTenenciaDTO(**payload.model_dump(exclude_unset=True))
    result = TenenciaService(db).update(cuenta_id, activo_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia no encontrada"
        )
    return result


@router.delete("/{cuenta_id}/{activo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenencia(cuenta_id: int, activo_id: int, db: Session = Depends(get_db)):
    deleted = TenenciaService(db).delete(cuenta_id, activo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenencia no encontrada"
        )