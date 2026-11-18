from pydantic import BaseModel
from decimal import Decimal


class CreateTenenciaGrupoDTO(BaseModel): # POST
    grupo_id: int
    activo_id: int
    cantidad: Decimal
    precio_promedio: Decimal


class UpdateTenenciaGrupoDTO(BaseModel): # PUT/PATCH
    cantidad: Decimal | None = None
    precio_promedio: Decimal | None = None


class DeleteTenenciaGrupoDTO(BaseModel): # DELETE
    grupo_id: int
    activo_id: int


class GetTenenciaGrupoDTO(BaseModel): # GET (individual)
    grupo_id: int
    activo_id: int


class TenenciaGrupoResponseDTO(BaseModel):
    grupo_id: int
    activo_id: int
    cantidad: Decimal
    precio_promedio: Decimal

    model_config = {"from_attributes": True}