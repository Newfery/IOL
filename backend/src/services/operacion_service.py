from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.db.models.operacion_model import Operacion
from src.db.models.cuenta_model import Cuenta
from src.db.models.activos_model import Activo
from src.db.models.tenencia_model import Tenencia
from src.db.models.inversor_model import Inversor
from src.mappers.operacion_mapper import OperacionMapper
from src.repositories.operacion_repository import OperacionRepository


class OperacionService:
    @staticmethod
    def _dinero(monto: Decimal) -> Decimal:
        return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def historial(
        db: Session,
        cuenta_id: int,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        tipo: str | None = None,
        ticker: str | None = None,
    ) -> dict[str, object]:
        operaciones = OperacionRepository.filtrar_operaciones(
            db, cuenta_id, fecha_desde, fecha_hasta, tipo, ticker
        )
        comisiones = OperacionRepository.obtener_total_comisiones(
            db, cuenta_id, fecha_desde, fecha_hasta
        )
        return {
            "operaciones": OperacionMapper.to_dto_list(operaciones),
            "total_comisiones": comisiones,
        }

    # Comprueba si el mercado está abierto
    @staticmethod
    def verificar_horario():

        ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))

        # Comprueba que sea de lunes a viernes
        if ahora.weekday() >= 5:
            raise HTTPException(
                status_code=400,
                detail="El mercado está cerrado los fines de semana"
            )

        # Comprueba que esté dentro del horario permitido
        hora = ahora.time()

        if not (hora >= datetime.strptime("11:00", "%H:%M").time()
                and hora <= datetime.strptime("17:00", "%H:%M").time()):

            raise HTTPException(
                status_code=400,
                detail="El mercado opera de 11:00 a 17:00"
            )

    # Verifica si el inversor puede comprar según su perfil de riesgo
    @staticmethod
    def verificar_riesgo(db: Session, cuenta: Cuenta, activo: Activo):

        inversor = db.query(Inversor).filter(
            Inversor.id == cuenta.inversor_id
        ).first()

        if inversor is None:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el inversor"
            )

        perfil = str(inversor.perfil_riesgo)

        if perfil == "conservador":
            riesgo_maximo = 2

        elif perfil == "moderado":
            riesgo_maximo = 4

        else:
            riesgo_maximo = 5

        nivel_riesgo = int(str(activo.nivel_riesgo))

        if nivel_riesgo > riesgo_maximo:
            raise HTTPException(
                status_code=400,
                detail="El activo supera el nivel de riesgo permitido para tu perfil"
            )

    # Obtiene el saldo correspondiente a la moneda del activo
    @staticmethod
    def obtener_saldo(cuenta: Cuenta, moneda: str):

        if moneda == "ARS":
            return cuenta.saldo_ars

        return cuenta.saldo_usd

    # Actualiza el saldo de la cuenta
    @staticmethod
    def actualizar_saldo(cuenta: Cuenta, moneda: str, monto: Decimal):

        if moneda == "ARS":
            cuenta.saldo_ars = monto  # type: ignore[assignment]

        else:
            cuenta.saldo_usd = monto  # type: ignore[assignment]

    # Realiza una compra de un activo
    @staticmethod
    def comprar(
        db: Session,
        cuenta_id: int,
        activo_id: int,
        cantidad: Decimal
    ):

        # Verifica el horario de operación
        OperacionService.verificar_horario()

        # Busca la cuenta
        cuenta = db.query(Cuenta).filter(
            Cuenta.id == cuenta_id
        ).first()

        if cuenta is None:
            raise HTTPException(
                status_code=404,
                detail="Cuenta no encontrada"
            )

        # Busca el activo
        activo = db.query(Activo).filter(
            Activo.id == activo_id
        ).first()

        if activo is None:
            raise HTTPException(
                status_code=404,
                detail="Activo no encontrado"
            )

        # Comprueba que el activo esté habilitado
        if not bool(activo.activo):
            raise HTTPException(
                status_code=400,
                detail="El activo está suspendido"
            )

        # Comprueba que la cantidad sea positiva
        cantidad = Decimal(str(cantidad))

        if cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor a cero"
            )

        # Comprueba el perfil de riesgo
        OperacionService.verificar_riesgo(db, cuenta, activo)

        # Calcula el monto y la comisión
        precio = Decimal(str(activo.precio_actual))
        monto = cantidad * precio
        comision = OperacionService._dinero(monto * Decimal("0.005"))
        total = OperacionService._dinero(monto + comision)

        # Comprueba que haya saldo suficiente
        moneda = str(activo.moneda)
        saldo = Decimal(str(
            OperacionService.obtener_saldo(cuenta, moneda)
        ))

        if saldo < total:
            raise HTTPException(
                status_code=400,
                detail="Saldo insuficiente para realizar la compra"
            )

        try:
            # Descuenta el dinero de la cuenta
            OperacionService.actualizar_saldo(
                cuenta,
                moneda,
                saldo - total
            )

            # Busca si ya existe una tenencia del activo
            tenencia = db.query(Tenencia).filter(
                Tenencia.cuenta_id == cuenta_id,
                Tenencia.activo_id == activo_id
            ).first()

            if tenencia:
                # Calcula el nuevo precio promedio ponderado
                nueva_cantidad = Decimal(str(tenencia.cantidad)) + cantidad

                nuevo_promedio = (
                    Decimal(str(tenencia.cantidad))
                    * Decimal(str(tenencia.precio_promedio))
                    + monto
                ) / nueva_cantidad

                tenencia.cantidad = nueva_cantidad  # type: ignore[assignment]
                tenencia.precio_promedio = nuevo_promedio  # type: ignore[assignment]

            else:
                # Crea una nueva tenencia
                tenencia = Tenencia(
                    cuenta_id=cuenta_id,
                    activo_id=activo_id,
                    cantidad=cantidad,
                    precio_promedio=precio
                )

                db.add(tenencia)

            # Registra la operación
            operacion = Operacion(
                cuenta_id=cuenta_id,
                activo_id=activo_id,
                tipo="compra",
                cantidad=cantidad,
                precio_unitario=precio,
                comision=comision,
                total=total,
                estado="ejecutada"
            )

            db.add(operacion)

            db.commit()
            db.refresh(operacion)

            return operacion

        except Exception:
            db.rollback()
            raise

    # Realiza una venta de un activo
    @staticmethod
    def vender(
        db: Session,
        cuenta_id: int,
        activo_id: int,
        cantidad: Decimal
    ):

        # Verifica el horario de operación
        OperacionService.verificar_horario()

        # Busca la cuenta
        cuenta = db.query(Cuenta).filter(
            Cuenta.id == cuenta_id
        ).first()

        if cuenta is None:
            raise HTTPException(
                status_code=404,
                detail="Cuenta no encontrada"
            )

        # Busca el activo
        activo = db.query(Activo).filter(
            Activo.id == activo_id
        ).first()

        if activo is None:
            raise HTTPException(
                status_code=404,
                detail="Activo no encontrado"
            )

        # Comprueba que el activo esté habilitado
        if not bool(activo.activo):
            raise HTTPException(
                status_code=400,
                detail="El activo está suspendido"
            )

        # Comprueba que la cantidad sea positiva
        cantidad = Decimal(str(cantidad))

        if cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor a cero"
            )

        # Busca la tenencia del inversor
        tenencia = db.query(Tenencia).filter(
            Tenencia.cuenta_id == cuenta_id,
            Tenencia.activo_id == activo_id
        ).first()

        if tenencia is None or Decimal(str(tenencia.cantidad)) < cantidad:
            raise HTTPException(
                status_code=400,
                detail="No tenés suficientes unidades para vender"
            )

        # Calcula el monto, la comisión y el total
        precio = Decimal(str(activo.precio_actual))
        monto = cantidad * precio
        comision = OperacionService._dinero(monto * Decimal("0.005"))
        total = OperacionService._dinero(monto - comision)

        # Calcula la ganancia o pérdida realizada
        precio_promedio = Decimal(str(tenencia.precio_promedio))

        resultado = OperacionService._dinero(
            cantidad * (precio - precio_promedio) - comision
        )

        try:
            # Acredita el dinero en la cuenta
            moneda = str(activo.moneda)
            saldo = Decimal(str(
                OperacionService.obtener_saldo(cuenta, moneda)
            ))

            OperacionService.actualizar_saldo(
                cuenta,
                moneda,
                saldo + total
            )

            # Actualiza la cantidad de unidades
            nueva_cantidad = Decimal(str(tenencia.cantidad)) - cantidad

            if nueva_cantidad == 0:
                # Elimina la tenencia si ya no quedan unidades
                db.delete(tenencia)

            else:
                tenencia.cantidad = nueva_cantidad  # type: ignore[assignment]

            # Registra la operación
            operacion = Operacion(
                cuenta_id=cuenta_id,
                activo_id=activo_id,
                tipo="venta",
                cantidad=cantidad,
                precio_unitario=precio,
                comision=comision,
                total=total,
                resultado_realizado=resultado,
                estado="ejecutada"
            )

            db.add(operacion)

            db.commit()
            db.refresh(operacion)

            return operacion

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def convertir_mep(db: Session, cuenta_id: int, monto_ars: Decimal):
        OperacionService.verificar_horario()
        monto_ars = OperacionService._dinero(Decimal(str(monto_ars)))
        if monto_ars <= 0:
            raise HTTPException(
                status_code=400,
                detail="El monto en ARS debe ser al menos 0.01",
            )

        cuenta = (
            db.query(Cuenta)
            .filter(Cuenta.id == cuenta_id)
            .with_for_update()
            .first()
        )
        if cuenta is None:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        al30 = db.query(Activo).filter(Activo.ticker == "AL30").first()
        al30d = db.query(Activo).filter(Activo.ticker == "AL30D").first()
        if al30 is None or al30d is None:
            raise HTTPException(
                status_code=400,
                detail="Se requieren los activos AL30 y AL30D para operar MEP",
            )
        if str(al30.moneda) != "ARS" or str(al30d.moneda) != "USD":
            raise HTTPException(
                status_code=400,
                detail="AL30 debe cotizar en ARS y AL30D en USD",
            )
        if not bool(al30.activo) or not bool(al30d.activo):
            raise HTTPException(
                status_code=400,
                detail="AL30 o AL30D está suspendido",
            )
        OperacionService.verificar_riesgo(db, cuenta, al30)

        precio_ars = Decimal(str(al30.precio_actual))
        precio_usd = Decimal(str(al30d.precio_actual))
        cantidad = (monto_ars / precio_ars).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        if cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail="El monto no alcanza para comprar una unidad mínima de AL30",
            )

        monto_compra = OperacionService._dinero(cantidad * precio_ars)
        comision_compra = OperacionService._dinero(
            monto_compra * Decimal("0.005")
        )
        total_compra = monto_compra + comision_compra
        saldo_ars = Decimal(str(cuenta.saldo_ars))
        if saldo_ars < total_compra:
            raise HTTPException(
                status_code=400,
                detail="Saldo ARS insuficiente para realizar la operación MEP",
            )

        monto_venta = OperacionService._dinero(cantidad * precio_usd)
        comision_venta = OperacionService._dinero(
            monto_venta * Decimal("0.005")
        )
        total_venta = monto_venta - comision_venta
        tipo_cambio = precio_ars / precio_usd

        try:
            cuenta.saldo_ars = saldo_ars - total_compra  # type: ignore[assignment]
            cuenta.saldo_usd = (  # type: ignore[assignment]
                Decimal(str(cuenta.saldo_usd)) + total_venta
            )
            compra = Operacion(
                cuenta_id=cuenta_id,
                activo_id=al30.id,
                tipo="compra",
                cantidad=cantidad,
                precio_unitario=precio_ars,
                comision=comision_compra,
                total=total_compra,
                estado="ejecutada",
            )
            venta = Operacion(
                cuenta_id=cuenta_id,
                activo_id=al30d.id,
                tipo="venta",
                cantidad=cantidad,
                precio_unitario=precio_usd,
                comision=comision_venta,
                total=total_venta,
                estado="ejecutada",
            )
            db.add_all([compra, venta])
            db.commit()
            db.refresh(compra)
            db.refresh(venta)
            return {
                "tipo_cambio": tipo_cambio,
                "monto_ars_debitado": total_compra,
                "monto_usd_acreditado": total_venta,
                "operaciones": [
                    OperacionService._operacion_a_dict(compra),
                    OperacionService._operacion_a_dict(venta),
                ],
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _operacion_a_dict(operacion: Operacion) -> dict[str, object]:
        return {
            "id": operacion.id,
            "cuenta_id": operacion.cuenta_id,
            "activo_id": operacion.activo_id,
            "tipo": operacion.tipo,
            "cantidad": operacion.cantidad,
            "precio_unitario": operacion.precio_unitario,
            "comision": operacion.comision,
            "total": operacion.total,
            "estado": operacion.estado,
            "fecha": operacion.fecha,
        }