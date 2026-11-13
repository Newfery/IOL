from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Literal

from src.db.connection import get_db
from src.dtos.cuenta_dto import (
    CreateCuentaDTO,
    CuentaResponseDTO,
    UpdateCuentaDTO,
)
from src.schemas.cuenta_schema import CreateCuentaSchema, UpdateCuentaSchema
from src.schemas.mep_schema import MEPRequestSchema
from src.services.cuenta_service import CuentaService
from src.services.operacion_service import OperacionService

router = APIRouter(prefix="/cuentas", tags=["cuentas"])


@router.post("/", response_model=CuentaResponseDTO, status_code=status.HTTP_201_CREATED)
def create_cuenta(payload: CreateCuentaSchema, db: Session = Depends(get_db)):
    dto = CreateCuentaDTO(**payload.model_dump())
    return CuentaService(db).create(dto)


@router.get("/", response_model=list[CuentaResponseDTO])
def list_cuentas(db: Session = Depends(get_db)):
    return CuentaService(db).list_all()


@router.post("/{cuenta_id}/mep")
def convertir_mep(
    cuenta_id: int,
    payload: MEPRequestSchema,
    db: Session = Depends(get_db),
):
    return OperacionService.convertir_mep(db, cuenta_id, payload.monto_ars)


@router.get("/{cuenta_id}/cartera")
def get_cartera(cuenta_id: int, db: Session = Depends(get_db)):
    result = CuentaService(db).cartera(cuenta_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return result


@router.get("/{cuenta_id}/ganancias-realizadas")
def get_ganancias_realizadas(cuenta_id: int, db: Session = Depends(get_db)):
    result = CuentaService(db).ganancias_realizadas(cuenta_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return result


@router.get("/{cuenta_id}/operaciones")
def get_operaciones(
    cuenta_id: int,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    tipo: Literal["compra", "venta"] | None = None,
    ticker: str | None = None,
    db: Session = Depends(get_db),
):
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="fecha_desde no puede ser posterior a fecha_hasta",
        )
    if CuentaService(db).get_by_id(cuenta_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return OperacionService.historial(
        db, cuenta_id, fecha_desde, fecha_hasta, tipo, ticker
    )


@router.get("/{cuenta_id}", response_model=CuentaResponseDTO)
def get_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    result = CuentaService(db).get_by_id(cuenta_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return result


@router.put("/{cuenta_id}", response_model=CuentaResponseDTO)
def replace_cuenta(
    cuenta_id: int,
    payload: CreateCuentaSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateCuentaDTO(**payload.model_dump())
    result = CuentaService(db).update(cuenta_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return result


@router.patch("/{cuenta_id}", response_model=CuentaResponseDTO)
def update_cuenta(
    cuenta_id: int,
    payload: UpdateCuentaSchema,
    db: Session = Depends(get_db),
):
    dto = UpdateCuentaDTO(**payload.model_dump(exclude_unset=True))
    result = CuentaService(db).update(cuenta_id, dto)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return result


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    deleted = CuentaService(db).delete(cuenta_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
