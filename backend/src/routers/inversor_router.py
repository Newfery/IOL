from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.inversor_dto import CreateInversorDTO, UpdateInversorDTO, InversorResponseDTO
from src.schemas.inversor_schema import CreateInversorSchema, UpdateInversorSchema
from src.services.inversor_service import InversorService

router = APIRouter(prefix="/inversores", tags=["inversores"])


@router.post("/", response_model=InversorResponseDTO, status_code=status.HTTP_201_CREATED)
def create_inversor(payload: CreateInversorSchema, db: Session = Depends(get_db)):
    """Valida con Schema, arma DTO y llama al service."""
    dto = CreateInversorDTO(**payload.model_dump())
    return InversorService(db).create(dto)


@router.get("/{inversor_id}", response_model=InversorResponseDTO)
def get_inversor(inversor_id: int, db: Session = Depends(get_db)):
    result = InversorService(db).get_by_id(inversor_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inversor no encontrado"
        )
    return result


@router.put("/{inversor_id}", response_model=InversorResponseDTO)
def update_inversor(inversor_id: int, payload: CreateInversorSchema, db: Session = Depends(get_db)):
    dto = UpdateInversorDTO(**payload.model_dump())
    result = InversorService(db).update(inversor_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inversor no encontrado"
        )
    return result


@router.patch("/{inversor_id}", response_model=InversorResponseDTO)
def patch_inversor(inversor_id: int, payload: UpdateInversorSchema, db: Session = Depends(get_db)):
    dto = UpdateInversorDTO(**payload.model_dump(exclude_unset=True))
    result = InversorService(db).update(inversor_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inversor no encontrado"
        )
    return result


@router.delete("/{inversor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inversor(inversor_id: int, db: Session = Depends(get_db)):
    deleted = InversorService(db).delete(inversor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inversor no encontrado"
        )