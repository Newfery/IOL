from pydantic import BaseModel
from decimal import Decimal


class CreateTenenciaDTO(BaseModel): # POST
    cuenta_id: int
    activo_id: int
    cantidad: Decimal
    precio_promedio: Decimal


class UpdateTenenciaDTO(BaseModel): # PUT/PATCH
    cantidad: Decimal | None = None
    precio_promedio: Decimal | None = None


class DeleteTenenciaDTO(BaseModel): # DELETE
    cuenta_id: int
    activo_id: int


class GetTenenciaDTO(BaseModel): # GET (individual)
    cuenta_id: int
    activo_id: int


class TenenciaResponseDTO(BaseModel):
    cuenta_id: int
    activo_id: int
    cantidad: Decimal
    precio_promedio: Decimal

    model_config = {"from_attributes": True}