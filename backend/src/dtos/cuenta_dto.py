from decimal import Decimal

from pydantic import BaseModel


class CreateCuentaDTO(BaseModel):  # POST
    titular: str
    numero_cuenta: str
    tipo_cuenta: str
    moneda: str
    saldo: Decimal = Decimal("0")
    cbu: str | None = None
    alias: str | None = None


class UpdateCuentaDTO(BaseModel):  # PUT/PATCH
    titular: str | None = None
    numero_cuenta: str | None = None
    tipo_cuenta: str | None = None
    moneda: str | None = None
    saldo: Decimal | None = None
    cbu: str | None = None
    alias: str | None = None


class DeleteCuentaDTO(BaseModel):  # DELETE
    id: int


class GetCuentaDTO(BaseModel):  # GET (individual)
    id: int


class CuentaResponseDTO(BaseModel):
    id: int
    titular: str
    numero_cuenta: str
    tipo_cuenta: str
    moneda: str
    saldo: Decimal
    cbu: str | None = None
    alias: str | None = None

    model_config = {"from_attributes": True}
