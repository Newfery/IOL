from decimal import Decimal

from pydantic import BaseModel, Field


class CreateCuentaDTO(BaseModel):  # POST
    inversor_id: int
    numero_comitente: str = Field(max_length=50)
    saldo_ars: Decimal = Field(default=Decimal("0.00"), ge=0)
    saldo_usd: Decimal = Field(default=Decimal("0.00"), ge=0)


class UpdateCuentaDTO(BaseModel):  # PUT/PATCH
    inversor_id: int | None = None
    numero_comitente: str | None = Field(default=None, max_length=50)
    saldo_ars: Decimal | None = Field(default=None, ge=0)
    saldo_usd: Decimal | None = Field(default=None, ge=0)


class DeleteCuentaDTO(BaseModel):  # DELETE
    id: int


class GetCuentaDTO(BaseModel):  # GET (individual)
    id: int


class CuentaResponseDTO(BaseModel):
    id: int
    inversor_id: int
    numero_comitente: str
    saldo_ars: Decimal
    saldo_usd: Decimal

    model_config = {"from_attributes": True}
