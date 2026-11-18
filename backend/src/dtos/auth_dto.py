from pydantic import BaseModel

from src.dtos.inversor_dto import InversorResponseDTO
from src.dtos.user_dto import UserResponseDTO


class LoginDTO(BaseModel):
    email: str
    password: str


class TokenDTO(BaseModel):
    token: str
    inversor: InversorResponseDTO
    token_type: str = "bearer"


class AdminTokenDTO(BaseModel):
    token: str
    user: UserResponseDTO
    token_type: str = "bearer"
