from pydantic import BaseModel, EmailStr

from src.dtos.inversor_dto import InversorResponseDTO
from src.dtos.user_dto import UserResponseDTO


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    token: str
    inversor: InversorResponseDTO
    token_type: str = "bearer"


class AdminTokenSchema(BaseModel):
    token: str
    user: UserResponseDTO
    token_type: str = "bearer"
