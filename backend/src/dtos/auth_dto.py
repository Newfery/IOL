from pydantic import BaseModel

from src.dtos.inversor_dto import InversorResponseDTO


class LoginDTO(BaseModel):
    email: str
    password: str


class TokenDTO(BaseModel):
    token: str
    inversor: InversorResponseDTO
    token_type: str = "bearer"
