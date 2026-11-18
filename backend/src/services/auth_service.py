from sqlalchemy.orm import Session

from src.dtos.auth_dto import AdminTokenDTO, LoginDTO, TokenDTO
from src.repositories.inversor_repository import InversorRepository
from src.repositories.user_repository import UserRepository
from src.mappers.inversor_mapper import to_inversor_response
from src.mappers.user_mapper import to_user_response
from src.utils.errors import UnauthorizedError
from src.utils.hash import verify_password
from src.utils.jwt import create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.repo = InversorRepository(db)
        self.user_repo = UserRepository(db)

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

    def login_admin(self, dto: LoginDTO) -> AdminTokenDTO:
        user = self.user_repo.find_by_email(dto.email)
        if (
            user is None
            or not user.is_admin
            or not verify_password(dto.password, user.password_hash)
        ):
            raise UnauthorizedError("Invalid credentials")

        token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role": "admin"}
        )
        return AdminTokenDTO(token=token, user=to_user_response(user))
