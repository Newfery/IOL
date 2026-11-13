from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos.activo_dto import (
    ActivoResponseDTO,
    CreateActivoDTO,
    UpdateActivoDTO,
)
from src.mappers.activos_mapper import activo_a_dto
from src.repositories.activos_repository import ActivoRepository
from src.utils.errors import ConflictError


class ActivoService:
    def __init__(self, db: Session):
        self.repo = ActivoRepository(db)

    def create(self, dto: CreateActivoDTO) -> ActivoResponseDTO:
        if self.repo.get_by_ticker(dto.ticker) is not None:
            raise ConflictError("El ticker ya está registrado")
        try:
            activo = self.repo.create(**dto.model_dump())
        except IntegrityError as exc:
            self.repo.db.rollback()
            raise ConflictError("El ticker ya está registrado") from exc
        return activo_a_dto(activo)

    def mas_operados(self) -> list[dict[str, object]]:
        return [
            {
                "activo": activo_a_dto(activo),
                "volumen": volumen,
            }
            for activo, volumen in self.repo.get_mas_operados()
        ]

    def get_all(
        self,
        tipo: str | None = None,
        moneda: str | None = None,
    ) -> list[ActivoResponseDTO]:
        activos = self.repo.get_all(tipo=tipo, moneda=moneda)
        return [activo_a_dto(activo) for activo in activos]

    def get_by_id(self, activo_id: int) -> ActivoResponseDTO | None:
        activo = self.repo.get_by_id(activo_id)
        if activo is None:
            return None
        return activo_a_dto(activo)

    def update(
        self,
        activo_id: int,
        dto: UpdateActivoDTO,
    ) -> ActivoResponseDTO | None:
        activo = self.repo.get_by_id(activo_id)
        if activo is None:
            return None

        for campo, valor in dto.model_dump(exclude_unset=True).items():
            if valor is not None:
                setattr(activo, campo, valor)

        actualizado = self.repo.update(activo)
        return activo_a_dto(actualizado)

    def delete(self, activo_id: int) -> bool:
        activo = self.repo.get_by_id(activo_id)
        if activo is None:
            return False

        self.repo.delete(activo)
        return True