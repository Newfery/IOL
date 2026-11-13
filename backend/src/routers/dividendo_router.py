from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.dtos.dividendo_dto import CreateDividendoDTO, DividendoResponseDTO
from src.middlewares.auth_middleware import get_current_admin
from src.schemas.dividendo_schema import CreateDividendoSchema
from src.services.dividendo_service import DividendoService

router = APIRouter(prefix="/dividendos", tags=["dividendos"])


@router.post(
    "/",
    response_model=DividendoResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def registrar_pago_dividendo(
    payload: CreateDividendoSchema,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    dto = CreateDividendoDTO(**payload.model_dump())
    return DividendoService(db).registrar_pago(dto)
