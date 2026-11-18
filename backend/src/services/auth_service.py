from sqlalchemy.orm import Session

from src.dtos.auth_dto import LoginDTO, TokenDTO
from src.repositories.inversor_repository import InversorRepository
from src.mappers.inversor_mapper import to_inversor_response
from src.utils.errors import UnauthorizedError
from src.utils.hash import verify_password
from src.utils.jwt import create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.repo = InversorRepository(db)

    def login(self, dto: LoginDTO) -> TokenDTO:
        inversor = self.repo.get_by_email(dto.email)
        if (
            inversor is None
            or not inversor.password_hash
            or not verify_password(dto.password, inversor.password_hash)
        ):
            raise UnauthorizedError("Invalid credentials")

        token = create_access_token({"sub": str(inversor.id), "email": inversor.email, "role": "inversor"})
        return TokenDTO(token=token, inversor=to_inversor_response(inversor))
