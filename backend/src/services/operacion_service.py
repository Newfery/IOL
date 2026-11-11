from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.db.models.operacion_model import Operacion
from src.db.models.cuenta_model import Cuenta
from src.db.models.activos_model import Activo
from src.db.models.tenencia_model import Tenencia
from src.db.models.inversor_model import Inversor


class OperacionService:

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
        if not bool(activo.activos):
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
        comision = monto * Decimal("0.005")
        total = monto + comision

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
        comision = monto * Decimal("0.005")
        total = monto - comision

        # Calcula la ganancia o pérdida realizada
        precio_promedio = Decimal(str(tenencia.precio_promedio))

        resultado = (
            cantidad * (precio - precio_promedio)
        ) - comision

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