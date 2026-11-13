from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.favoritos_dto import CreateFavoritoDTO, FavoritoResponseDTO
from src.mappers.favoritos_mapper import to_favorito_response
from src.repositories.favoritos_repository import FavoritosRepository
from src.utils.errors import ConflictError, NotFoundError


class FavoritosService:
    def __init__(self, db: Session):
        self.repo = FavoritosRepository(db)

    def create(self, dto: CreateFavoritoDTO) -> FavoritoResponseDTO:
        if not self.repo.inversor_exists(dto.inversor_id):
            raise NotFoundError("Inversor no encontrado")
        if not self.repo.activo_exists(dto.activo_id):
            raise NotFoundError("Activo no encontrado")
        if self.repo.get_by_id(dto.inversor_id, dto.activo_id) is not None:
            raise ConflictError("El activo ya está en favoritos")

        try:
            favorito = self.repo.create(dto.inversor_id, dto.activo_id)
        except IntegrityError as exc:
            if self.repo.get_by_id(dto.inversor_id, dto.activo_id) is not None:
                raise ConflictError("El activo ya está en favoritos") from exc
            raise
        return to_favorito_response(favorito)

    def get_by_id(self, inversor_id: int, activo_id: int) -> FavoritoResponseDTO | None:
        favorito = self.repo.get_by_id(inversor_id, activo_id)
        if favorito is None:
            return None
        return to_favorito_response(favorito)

    def get_by_inversor(self, inversor_id: int) -> list[FavoritoResponseDTO]:
        if not self.repo.inversor_exists(inversor_id):
            raise NotFoundError("Inversor no encontrado")
        return [
            to_favorito_response(favorito)
            for favorito in self.repo.get_by_inversor(inversor_id)
        ]

    def delete(self, inversor_id: int, activo_id: int) -> bool:
        favorito = self.repo.get_by_id(inversor_id, activo_id)
        if favorito is None:
            return False
        self.repo.delete(favorito)
        return True
