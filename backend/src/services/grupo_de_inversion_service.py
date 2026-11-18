from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.grupo_de_inversion_dto import (
    CreateGrupoDeInversionDTO,
    GrupoDeInversionResponseDTO,
    UpdateGrupoDeInversionDTO,
)
from src.mappers.grupo_de_inversion_mapper import to_grupo_de_inversion_response
from src.repositories.grupo_de_inversion_repository import GrupoDeInversionRepository
from src.utils.errors import ConflictError
from src.utils.integrity_errors import is_unique_violation


class GrupoDeInversionService:
    def __init__(self, db: Session):
        self.repo = GrupoDeInversionRepository(db)

    def create(
        self,
        dto: CreateGrupoDeInversionDTO,
    ) -> GrupoDeInversionResponseDTO:
        if not self.repo.inversor_exists(dto.creador_id):
            raise ConflictError("El inversor creador no existe")
        if self.repo.find_by_nombre(dto.nombre) is not None:
            raise ConflictError("El nombre del grupo ya está en uso")
        if self.repo.find_by_codigo_union(dto.codigo_union) is not None:
            raise ConflictError("El código de unión ya está en uso")

        try:
            grupo = self.repo.create(
                nombre=dto.nombre,
                codigo_union=dto.codigo_union,
                creador_id=dto.creador_id,
                plata_disponible=dto.plata_disponible,
            )
        except IntegrityError as exc:
            self.repo.db.rollback()
            if is_unique_violation(exc):
                raise ConflictError(
                    "El nombre o el código de unión ya está en uso"
                ) from exc
            raise
        return to_grupo_de_inversion_response(grupo)

    def get_by_id(self, grupo_id: int) -> GrupoDeInversionResponseDTO | None:
        grupo = self.repo.find_by_id(grupo_id)
        if grupo is None:
            return None
        return to_grupo_de_inversion_response(grupo)

    def list_all(self) -> list[GrupoDeInversionResponseDTO]:
        return [
            to_grupo_de_inversion_response(grupo)
            for grupo in self.repo.list_all()
        ]

    def update(
        self,
        grupo_id: int,
        dto: UpdateGrupoDeInversionDTO,
    ) -> GrupoDeInversionResponseDTO | None:
        grupo = self.repo.find_by_id(grupo_id)
        if grupo is None:
            return None

        fields = dto.model_dump(exclude_unset=True)
        if "creador_id" in fields and not self.repo.inversor_exists(
            fields["creador_id"]
        ):
            raise ConflictError("El inversor creador no existe")

        for field, value in fields.items():
            setattr(grupo, field, value)
        if "creador_id" in fields:
            self.repo.ensure_creator_membership(
                grupo_id,
                fields["creador_id"],
            )

        try:
            updated = self.repo.update(grupo)
        except IntegrityError as exc:
            self.repo.db.rollback()
            if is_unique_violation(exc):
                raise ConflictError(
                    "El nombre o el código de unión ya está en uso"
                ) from exc
            raise
        return to_grupo_de_inversion_response(updated)

    def delete(self, grupo_id: int) -> bool:
        grupo = self.repo.find_by_id(grupo_id)
        if grupo is None:
            return False
        self.repo.delete(grupo)
        return True
