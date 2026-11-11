from pydantic import BaseModel, EmailStr, Field


class CreateInversorSchema(BaseModel):
    nombre: str = Field(min_length=2)
    email: EmailStr
    cuit: str = Field(min_length=11, max_length=11, pattern=r"^[0-9]{11}$")
    perfil_riesgo: str = Field(pattern=r"^(conservador|moderado|agresivo)$")


class UpdateInversorSchema(BaseModel):
    nombre: str | None = Field(default=None, min_length=2)
    email: EmailStr | None = None
    cuit: str | None = Field(default=None, min_length=11, max_length=11, pattern=r"^[0-9]{11}$")
    perfil_riesgo: str | None = Field(
        default=None,
        pattern=r"^(conservador|moderado|agresivo)$"
    )


class DeleteInversorSchema(BaseModel):
    id: int


class GetInversorSchema(BaseModel):
    id: int