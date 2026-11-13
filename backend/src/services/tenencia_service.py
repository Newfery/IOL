from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.tenencia_dto import CreateTenenciaDTO, UpdateTenenciaDTO, TenenciaResponseDTO
from src.mappers.tenencia_mapper import to_tenencia_response
from src.repositories.tenencia_repository import TenenciaRepository
from src.utils.errors import ConflictError
from src.utils.integrity_errors import is_unique_violation


class TenenciaService:
    def __init__(self, db: Session):
        self.repo = TenenciaRepository(db)

    def create(self, dto: CreateTenenciaDTO) -> TenenciaResponseDTO:
        try:
            tenencia = self.repo.create(
                cuenta_id=dto.cuenta_id,
                activo_id=dto.activo_id,
                cantidad=dto.cantidad,
                precio_promedio=dto.precio_promedio
            )
        except IntegrityError as exc:
            self.repo.db.rollback()
            if is_unique_violation(exc):
                raise ConflictError(
                    "Ya existe una tenencia para esta cuenta y este activo"
                ) from exc
            raise
        return to_tenencia_response(tenencia)

    def get_by_id(self, cuenta_id: int, activo_id: int) -> TenenciaResponseDTO | None:
        tenencia = self.repo.get_by_id(cuenta_id, activo_id)
        if tenencia is None:
            return None
        return to_tenencia_response(tenencia)

    def update(self, cuenta_id: int, activo_id: int, dto: UpdateTenenciaDTO) -> TenenciaResponseDTO | None:
        tenencia = self.repo.get_by_id(cuenta_id, activo_id)
        if tenencia is None:
            return None

        tenencia.cantidad = dto.cantidad if dto.cantidad is not None else tenencia.cantidad
        tenencia.precio_promedio = dto.precio_promedio if dto.precio_promedio is not None else tenencia.precio_promedio

        updated = self.repo.update(tenencia)
        return to_tenencia_response(updated)

    def delete(self, cuenta_id: int, activo_id: int) -> bool:
        tenencia = self.repo.get_by_id(cuenta_id, activo_id)
        if tenencia is None:
            return False

        self.repo.delete(tenencia)
        return True