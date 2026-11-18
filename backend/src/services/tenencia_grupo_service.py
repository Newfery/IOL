from sqlalchemy.orm import Session

from src.dtos.tenencia_grupo_dto import CreateTenenciaGrupoDTO, UpdateTenenciaGrupoDTO, TenenciaGrupoResponseDTO
from src.mappers.tenencia_grupo_mapper import to_tenencia_grupo_response
from src.repositories.tenencia_grupo_repository import TenenciaGrupoRepository


class TenenciaGrupoService:
    def __init__(self, db: Session):
        self.repo = TenenciaGrupoRepository(db)

    def create(self, dto: CreateTenenciaGrupoDTO) -> TenenciaGrupoResponseDTO:
        tenencia_grupo = self.repo.create(
            grupo_id=dto.grupo_id,
            activo_id=dto.activo_id,
            cantidad=dto.cantidad,
            precio_promedio=dto.precio_promedio
        )
        return to_tenencia_grupo_response(tenencia_grupo)

    def get_by_id(self, grupo_id: int, activo_id: int) -> TenenciaGrupoResponseDTO | None:
        tenencia_grupo = self.repo.get_by_id(grupo_id, activo_id)

        if tenencia_grupo is None:
            return None

        return to_tenencia_grupo_response(tenencia_grupo)

    def update(self, grupo_id: int, activo_id: int, dto: UpdateTenenciaGrupoDTO) -> TenenciaGrupoResponseDTO | None:
        tenencia_grupo = self.repo.get_by_id(grupo_id, activo_id)

        if tenencia_grupo is None:
            return None

        tenencia_grupo.cantidad = dto.cantidad if dto.cantidad is not None else tenencia_grupo.cantidad
        tenencia_grupo.precio_promedio = dto.precio_promedio if dto.precio_promedio is not None else tenencia_grupo.precio_promedio

        updated = self.repo.update(tenencia_grupo)
        return to_tenencia_grupo_response(updated)

    def delete(self, grupo_id: int, activo_id: int) -> bool:
        tenencia_grupo = self.repo.get_by_id(grupo_id, activo_id)

        if tenencia_grupo is None:
            return False

        self.repo.delete(tenencia_grupo)
        return True