from src.db.models.tenencia_grupo_model import TenenciaGrupo
from src.dtos.tenencia_grupo_dto import TenenciaGrupoResponseDTO


def to_tenencia_grupo_response(tenencia_grupo: TenenciaGrupo) -> TenenciaGrupoResponseDTO:
    """Convierte un Model SQLAlchemy en un DTO de respuesta."""
    return TenenciaGrupoResponseDTO.model_validate(tenencia_grupo)