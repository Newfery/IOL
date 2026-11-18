from fastapi import Depends, Header
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models.user_model import User
from src.db.models.inversor_model import Inversor
from src.repositories.inversor_repository import InversorRepository
from src.repositories.user_repository import UserRepository
from src.utils.errors import ForbiddenError, UnauthorizedError
from src.utils.jwt import decode_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)

    if payload.get("role") != "admin":
        raise ForbiddenError("Se requiere una cuenta de administrador")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    try:
        user = UserRepository(db).find_by_id(int(user_id))
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Invalid token payload") from exc
    if user is None:
        raise UnauthorizedError("User no longer exists")

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise ForbiddenError("Se requiere una cuenta de administrador")
    return current_user


def get_current_inversor(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Inversor:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload.get("role") != "inversor" or payload.get("sub") is None:
        raise UnauthorizedError("Invalid token payload")
    try:
        inversor_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Invalid token payload") from exc
    inversor = InversorRepository(db).get_by_id(inversor_id)
    if inversor is None:
        raise UnauthorizedError("Inversor no longer exists")
    return inversor
