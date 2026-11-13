from decimal import Decimal
from typing import TypedDict

from sqlalchemy.orm import Session

from src.dtos.cuenta_dto import (
    CreateCuentaDTO,
    CuentaResponseDTO,
    UpdateCuentaDTO,
)
from src.mappers.cuenta_mapper import to_cuenta_response
from src.repositories.cuenta_repository import CuentaRepository


class ValorizacionPorMoneda(TypedDict):
    ARS: Decimal
    USD: Decimal


class TenenciaCartera(TypedDict):
    activo_id: int
    ticker: str
    tipo: str
    moneda: str
    cantidad: Decimal
    precio_promedio: Decimal
    precio_actual: Decimal
    valor_actual: Decimal
    rendimiento_porcentual: Decimal | None


class CarteraResponse(TypedDict):
    cuenta_id: int
    tenencias: list[TenenciaCartera]
    total_valorizado: ValorizacionPorMoneda
    saldos_disponibles: ValorizacionPorMoneda
    total_cartera: ValorizacionPorMoneda
    composicion_por_tipo: dict[str, dict[str, Decimal]]


class GananciaAnual(TypedDict):
    anio: int
    resultado_realizado: Decimal


class GananciasRealizadasResponse(TypedDict):
    cuenta_id: int
    ganancias_por_anio: list[GananciaAnual]


class CuentaService:
    def __init__(self, db: Session):
        self.repo = CuentaRepository(db)

    def create(self, dto: CreateCuentaDTO) -> CuentaResponseDTO:
        cuenta = self.repo.create(
            inversor_id=dto.inversor_id,
            numero_comitente=dto.numero_comitente,
            saldo_ars=dto.saldo_ars,
            saldo_usd=dto.saldo_usd,
        )
        return to_cuenta_response(cuenta)

    def get_by_id(self, cuenta_id: int) -> CuentaResponseDTO | None:
        cuenta = self.repo.find_by_id(cuenta_id)
        if cuenta is None:
            return None
        return to_cuenta_response(cuenta)

    def list_all(self) -> list[CuentaResponseDTO]:
        return [
            to_cuenta_response(cuenta)
            for cuenta in self.repo.list_all()
        ]

    def cartera(self, cuenta_id: int) -> CarteraResponse | None:
        cuenta = self.repo.find_by_id(cuenta_id)
        if cuenta is None:
            return None

        tenencias: list[TenenciaCartera] = []
        valores_por_moneda: ValorizacionPorMoneda = {
            "ARS": Decimal("0"),
            "USD": Decimal("0"),
        }
        valores_por_tipo: dict[str, dict[str, Decimal]] = {
            "ARS": {},
            "USD": {},
        }

        for tenencia, activo in self.repo.list_tenencias(cuenta_id):
            cantidad = Decimal(str(tenencia.cantidad))
            promedio = Decimal(str(tenencia.precio_promedio))
            precio_actual = Decimal(str(activo.precio_actual))
            moneda = str(activo.moneda)
            tipo = str(activo.tipo)
            valor_actual = cantidad * precio_actual
            rendimiento = (
                ((precio_actual - promedio) / promedio * Decimal("100"))
                if promedio > 0 else None
            )

            valores_por_moneda[moneda] += valor_actual
            valores_por_tipo[moneda][tipo] = (
                valores_por_tipo[moneda].get(tipo, Decimal("0"))
                + valor_actual
            )
            tenencia_cartera: TenenciaCartera = {
                "activo_id": int(str(activo.id)),
                "ticker": str(activo.ticker),
                "tipo": tipo,
                "moneda": moneda,
                "cantidad": cantidad,
                "precio_promedio": promedio,
                "precio_actual": precio_actual,
                "valor_actual": valor_actual,
                "rendimiento_porcentual": rendimiento,
            }
            tenencias.append(tenencia_cartera)

        composicion: dict[str, dict[str, Decimal]] = {"ARS": {}, "USD": {}}
        for moneda, tipos in valores_por_tipo.items():
            total = valores_por_moneda[moneda]
            if total > 0:
                composicion[moneda] = {
                    tipo: valor / total * Decimal("100")
                    for tipo, valor in tipos.items()
                }

        saldos: ValorizacionPorMoneda = {
            "ARS": Decimal(str(cuenta.saldo_ars)),
            "USD": Decimal(str(cuenta.saldo_usd)),
        }
        totales_cartera: ValorizacionPorMoneda = {
            "ARS": valores_por_moneda["ARS"] + saldos["ARS"],
            "USD": valores_por_moneda["USD"] + saldos["USD"],
        }
        return {
            "cuenta_id": cuenta_id,
            "tenencias": tenencias,
            "total_valorizado": valores_por_moneda,
            "saldos_disponibles": saldos,
            "total_cartera": totales_cartera,
            "composicion_por_tipo": composicion,
        }

    def ganancias_realizadas(
        self, cuenta_id: int
    ) -> GananciasRealizadasResponse | None:
        if self.repo.find_by_id(cuenta_id) is None:
            return None
        ganancias: list[GananciaAnual] = [
            {"anio": int(anio), "resultado_realizado": Decimal(str(total))}
            for anio, total in self.repo.realized_gains_by_year(cuenta_id)
        ]
        return {
            "cuenta_id": cuenta_id,
            "ganancias_por_anio": ganancias,
        }

    def update(
        self,
        cuenta_id: int,
        dto: UpdateCuentaDTO,
    ) -> CuentaResponseDTO | None:
        fields: dict[str, int | str | Decimal] = dto.model_dump(exclude_unset=True)
        cuenta = self.repo.update(cuenta_id, **fields)
        if cuenta is None:
            return None
        return to_cuenta_response(cuenta)

    def delete(self, cuenta_id: int) -> bool:
        return self.repo.delete(cuenta_id)
