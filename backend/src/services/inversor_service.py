from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.inversor_dto import CreateInversorDTO, UpdateInversorDTO, InversorResponseDTO
from src.mappers.inversor_mapper import to_inversor_response
from src.repositories.inversor_repository import InversorRepository
from src.utils.errors import ConflictError


class InversorService:
    def __init__(self, db: Session):
        self.repo = InversorRepository(db)

    def create(self, dto: CreateInversorDTO) -> InversorResponseDTO:
        if self.repo.get_by_email(dto.email) is not None:
            raise ConflictError("Este email ya está en uso")
        if self.repo.get_by_cuit(dto.cuit) is not None:
            raise ConflictError("Este CUIT ya está en uso")
        try:
            inversor = self.repo.create(
                nombre=dto.nombre,
                email=dto.email,
                cuit=dto.cuit,
                perfil_riesgo=dto.perfil_riesgo
            )
        except IntegrityError as exc:
            self.repo.db.rollback()
            raise ConflictError("El email o CUIT ya está en uso") from exc
        return to_inversor_response(inversor)

    def get_by_id(self, inversor_id: int) -> InversorResponseDTO | None:
        inversor = self.repo.get_by_id(inversor_id)
        if inversor is None:
            return None
        return to_inversor_response(inversor)

    def get_by_email(self, email: str) -> InversorResponseDTO | None:
        inversor = self.repo.get_by_email(email)
        if inversor is None:
            return None
        return to_inversor_response(inversor)

    def update(self, inversor_id: int, dto: UpdateInversorDTO) -> InversorResponseDTO | None:
        inversor = self.repo.get_by_id(inversor_id)
        if inversor is None:
            return None

        for campo in ("nombre", "email", "cuit", "perfil_riesgo"):
            valor = getattr(dto, campo)
            if valor is not None:
                setattr(inversor, campo, valor)

        updated = self.repo.update(inversor)
        return to_inversor_response(updated)

    def delete(self, inversor_id: int) -> bool:
        inversor = self.repo.get_by_id(inversor_id)
        if inversor is None:
            return False

        self.repo.delete(inversor)
        return True