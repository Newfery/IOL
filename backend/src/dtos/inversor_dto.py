from pydantic import BaseModel
from datetime import date


class CreateInversorDTO(BaseModel): # POST
    nombre: str
    email: str
    cuit: str
    perfil_riesgo: str


class UpdateInversorDTO(BaseModel): # PUT/PATCH
    nombre: str | None = None
    email: str | None = None
    cuit: str | None = None
    perfil_riesgo: str | None = None


class DeleteInversorDTO(BaseModel): # DELETE
    id: int


class GetInversorDTO(BaseModel): # GET (individual)
    id: int


class InversorResponseDTO(BaseModel):
    id: int
    nombre: str
    email: str
    cuit: str
    perfil_riesgo: str
    fecha_alta: date

    model_config = {"from_attributes": True}