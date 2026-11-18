from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.auth_dto import AdminTokenDTO, LoginDTO, TokenDTO
from src.schemas.auth_schema import AdminTokenSchema, LoginSchema, TokenSchema
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenSchema)
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    dto = LoginDTO(**payload.model_dump())
    token: TokenDTO = AuthService(db).login(dto)
    return TokenSchema(**token.model_dump())


@router.post("/admin/login", response_model=AdminTokenSchema)
def admin_login(payload: LoginSchema, db: Session = Depends(get_db)):
    dto = LoginDTO(**payload.model_dump())
    token: AdminTokenDTO = AuthService(db).login_admin(dto)
    return AdminTokenSchema(**token.model_dump())
