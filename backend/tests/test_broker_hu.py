import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.connection import Base
from src.db.models.activos_model import Activo
from src.db.models.cuenta_model import Cuenta
from src.db.models.movimiento_model import Movimiento
from src.db.models.operacion_model import Operacion
from src.db.models.tenencia_model import Tenencia
from src.dtos.inversor_dto import CreateInversorDTO
from src.dtos.movimiento_dto import CreateMovimientoDTO
from src.services.cuenta_service import CuentaService
from src.services.inversor_service import InversorService
from src.services.movimiento_service import MovimientoService
from src.services.operacion_service import OperacionService
from src.utils.errors import BadRequestError


class BrokerHUIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def crear_cuenta(self, perfil: str = "agresivo") -> Cuenta:
        inversor = InversorService(self.db).create(
            CreateInversorDTO(
                nombre="Inversor Demo",
                email="demo@example.com",
                cuit="20123456789",
                perfil_riesgo=perfil,
            )
        )
        inversor_id = int(str(inversor.id))
        cuenta = self.db.query(Cuenta).filter(
            Cuenta.inversor_id == inversor_id
        ).one()
        return cuenta

    def crear_activo(
        self,
        ticker: str,
        moneda: str = "ARS",
        precio: str = "100",
        riesgo: int = 1,
    ) -> Activo:
        activo = Activo(
            ticker=ticker,
            nombre=ticker,
            tipo="bono",
            moneda=moneda,
            precio_actual=Decimal(precio),
            nivel_riesgo=riesgo,
            activo=True,
        )
        self.db.add(activo)
        self.db.commit()
        return activo

    def test_alta_inversor_crea_cuenta_vacia_con_comitente_unico(self):
        cuenta = self.crear_cuenta()

        self.assertTrue(cuenta.numero_comitente)
        self.assertEqual(cuenta.saldo_ars, Decimal("0.00"))
        self.assertEqual(cuenta.saldo_usd, Decimal("0.00"))

    def test_deposito_y_extraccion_actualizan_saldo_y_rechazan_exceso(self):
        cuenta = self.crear_cuenta()
        cuenta_id = int(str(cuenta.id))
        service = MovimientoService(self.db)
        service.create(CreateMovimientoDTO(
            cuenta_id=cuenta_id,
            tipo="deposito",
            moneda="ARS",
            monto=Decimal("100.00"),
        ))

        with self.assertRaises(BadRequestError):
            service.create(CreateMovimientoDTO(
                cuenta_id=cuenta_id,
                tipo="extraccion",
                moneda="ARS",
                monto=Decimal("100.01"),
            ))

        self.db.refresh(cuenta)
        self.assertEqual(cuenta.saldo_ars, Decimal("100.00"))
        self.assertEqual(self.db.query(Movimiento).count(), 1)

    def test_compra_registra_tenencia_y_descuenta_comision(self):
        cuenta = self.crear_cuenta()
        activo = self.crear_activo("TEST")
        cuenta_id = int(str(cuenta.id))
        activo_id = int(str(activo.id))
        setattr(cuenta, "saldo_ars", Decimal("500"))
        self.db.commit()

        with patch.object(OperacionService, "verificar_horario"):
            operacion = OperacionService.comprar(
                self.db, cuenta_id, activo_id, Decimal("2")
            )

        self.db.refresh(cuenta)
        tenencia = self.db.query(Tenencia).one()
        self.assertEqual(operacion.comision, Decimal("1.00"))
        self.assertEqual(operacion.total, Decimal("201.00"))
        self.assertEqual(cuenta.saldo_ars, Decimal("299.00"))
        self.assertEqual(tenencia.cantidad, Decimal("2.0000"))

    def test_mep_guarda_las_dos_patas_o_ninguna(self):
        cuenta = self.crear_cuenta()
        self.crear_activo("AL30", "ARS", "100")
        self.crear_activo("AL30D", "USD", "50")
        cuenta_id = int(str(cuenta.id))
        setattr(cuenta, "saldo_ars", Decimal("5000"))
        self.db.commit()

        with patch.object(OperacionService, "verificar_horario"):
            respuesta = OperacionService.convertir_mep(
                self.db, cuenta_id, Decimal("1000")
            )

        self.assertEqual(respuesta["tipo_cambio"], Decimal("2"))
        self.assertEqual(self.db.query(Operacion).count(), 2)
        self.db.refresh(cuenta)
        self.assertEqual(cuenta.saldo_ars, Decimal("3995.00"))
        self.assertEqual(cuenta.saldo_usd, Decimal("497.50"))

        setattr(cuenta, "saldo_ars", Decimal("10"))
        self.db.commit()
        with patch.object(OperacionService, "verificar_horario"):
            with self.assertRaises(HTTPException):
                OperacionService.convertir_mep(
                    self.db, cuenta_id, Decimal("1000")
                )
        self.assertEqual(self.db.query(Operacion).count(), 2)

    def test_cartera_y_ganancias_realizadas_se_calculan_por_moneda_y_anio(self):
        cuenta = self.crear_cuenta()
        activo = self.crear_activo("STOCK", "ARS", "120")
        cuenta_id = int(str(cuenta.id))
        activo_id = int(str(activo.id))
        self.db.add(Tenencia(
            cuenta_id=cuenta_id,
            activo_id=activo_id,
            cantidad=Decimal("2"),
            precio_promedio=Decimal("100"),
        ))
        self.db.add(Operacion(
            cuenta_id=cuenta_id,
            activo_id=activo_id,
            tipo="venta",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("120"),
            comision=Decimal("0.60"),
            total=Decimal("119.40"),
            resultado_realizado=Decimal("19.40"),
            fecha=datetime(2025, 6, 1),
            estado="ejecutada",
        ))
        setattr(cuenta, "saldo_ars", Decimal("50"))
        self.db.commit()

        cartera = CuentaService(self.db).cartera(cuenta_id)
        ganancias = CuentaService(self.db).ganancias_realizadas(cuenta_id)
        if cartera is None or ganancias is None:
            self.fail("La cuenta creada no debe desaparecer")

        self.assertEqual(
            cartera["total_valorizado"]["ARS"],
            Decimal("240"),
        )
        self.assertEqual(cartera["total_cartera"]["ARS"], Decimal("290"))
        self.assertEqual(
            cartera["composicion_por_tipo"]["ARS"]["bono"],
            Decimal("100"),
        )
        self.assertEqual(
            ganancias["ganancias_por_anio"][0]["anio"],
            2025,
        )
        self.assertEqual(
            ganancias["ganancias_por_anio"][0]["resultado_realizado"],
            Decimal("19.4"),
        )
