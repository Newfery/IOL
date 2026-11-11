from sqlalchemy.orm import Session

from src.dtos.inversor_dto import CreateInversorDTO, UpdateInversorDTO, InversorResponseDTO
from src.mappers.inversor_mapper import to_inversor_response
from src.repositories.inversor_repository import InversorRepository


class InversorService:
    def __init__(self, db: Session):
        self.repo = InversorRepository(db)

    def create(self, dto: CreateInversorDTO) -> InversorResponseDTO:
        inversor = self.repo.create(
            nombre=dto.nombre,
            email=dto.email,
            cuit=dto.cuit,
            perfil_riesgo=dto.perfil_riesgo
        )
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

        inversor.nombre = dto.nombre or inversor.nombre
        inversor.email = dto.email or inversor.email
        inversor.cuit = dto.cuit or inversor.cuit
        inversor.perfil_riesgo = dto.perfil_riesgo or inversor.perfil_riesgo

        updated = self.repo.update(inversor)
        return to_inversor_response(updated)

    def delete(self, inversor_id: int) -> bool:
        inversor = self.repo.get_by_id(inversor_id)
        if inversor is None:
            return False

        self.repo.delete(inversor)
        return True