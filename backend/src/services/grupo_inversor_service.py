from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.grupo_inversor_dto import (
    CreateGrupoInversorDTO,
    GrupoInversorResponseDTO,
)
from src.mappers.grupo_inversor_mapper import to_grupo_inversor_response
from src.repositories.grupo_inversor_repository import GrupoInversorRepository
from src.utils.errors import ConflictError, NotFoundError
from src.utils.integrity_errors import is_unique_violation


class GrupoInversorService:
    def __init__(self, db: Session):
        self.repo = GrupoInversorRepository(db)

    def create(self, dto: CreateGrupoInversorDTO) -> GrupoInversorResponseDTO:
        if not self.repo.group_exists(dto.grupo_id):
            raise NotFoundError("Grupo de inversión no encontrado")
        if not self.repo.inversor_exists(dto.inversor_id):
            raise NotFoundError("Inversor no encontrado")
        if self.repo.find_by_id(dto.grupo_id, dto.inversor_id) is not None:
            raise ConflictError("El inversor ya pertenece al grupo")

        try:
            integrante = self.repo.create(
                grupo_id=dto.grupo_id,
                inversor_id=dto.inversor_id,
                fecha_union=dto.fecha_union or datetime.now(),
            )
        except IntegrityError as exc:
            self.repo.db.rollback()
            if is_unique_violation(exc):
                raise ConflictError("El inversor ya pertenece al grupo") from exc
            raise
        return to_grupo_inversor_response(integrante)

    def get_by_id(
        self,
        grupo_id: int,
        inversor_id: int,
    ) -> GrupoInversorResponseDTO | None:
        integrante = self.repo.find_by_id(grupo_id, inversor_id)
        if integrante is None:
            return None
        return to_grupo_inversor_response(integrante)

    def get_by_grupo(self, grupo_id: int) -> list[GrupoInversorResponseDTO]:
        if not self.repo.group_exists(grupo_id):
            raise NotFoundError("Grupo de inversión no encontrado")
        return [
            to_grupo_inversor_response(integrante)
            for integrante in self.repo.find_by_grupo(grupo_id)
        ]

    def delete(self, grupo_id: int, inversor_id: int) -> bool:
        grupo = self.repo.find_group(grupo_id)
        if grupo is None:
            return False
        if grupo.creador_id == inversor_id:
            raise ConflictError("No se puede quitar al líder como integrante")
        integrante = self.repo.find_by_id(grupo_id, inversor_id)
        if integrante is None:
            return False
        self.repo.delete(integrante)
        return True
