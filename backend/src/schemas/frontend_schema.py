from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: str = Field(pattern="^(buy|sell)$")
    qty: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    price: Decimal = Field(gt=0, max_digits=15, decimal_places=4)


class GroupCredentialsRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=4, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar los 72 bytes")
        return value


class GroupContributionRequest(BaseModel):
    monto: Decimal = Field(gt=0, max_digits=15, decimal_places=2)


class GroupOperationRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    cantidad: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
