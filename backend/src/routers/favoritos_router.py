from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.favoritos_dto import CreateFavoritoDTO, FavoritoResponseDTO
from src.schemas.favoritos_schema import CreateFavoritoSchema
from src.services.favoritos_service import FavoritosService

router = APIRouter(prefix="/favoritos", tags=["favoritos"])


@router.post("/", response_model=FavoritoResponseDTO, status_code=status.HTTP_201_CREATED)
def create_favorito(payload: CreateFavoritoSchema, db: Session = Depends(get_db)):
    dto = CreateFavoritoDTO(**payload.model_dump())
    return FavoritosService(db).create(dto)


@router.get("/inversor/{inversor_id}", response_model=list[FavoritoResponseDTO])
def get_favoritos_by_inversor(inversor_id: int, db: Session = Depends(get_db)):
    return FavoritosService(db).get_by_inversor(inversor_id)


@router.get("/{inversor_id}/{activo_id}", response_model=FavoritoResponseDTO)
def get_favorito(inversor_id: int, activo_id: int, db: Session = Depends(get_db)):
    result = FavoritosService(db).get_by_id(inversor_id, activo_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorito no encontrado",
        )
    return result


@router.delete("/{inversor_id}/{activo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorito(inversor_id: int, activo_id: int, db: Session = Depends(get_db)):
    deleted = FavoritosService(db).delete(inversor_id, activo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorito no encontrado",
        )
