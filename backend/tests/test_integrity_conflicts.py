import unittest
from decimal import Decimal

from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.connection import Base
from src.db.models.activos_model import Activo
from src.db.models.cuenta_model import Cuenta
from src.db.models.inversor_model import Inversor
from src.db.models.tenencia_model import Tenencia
from src.dtos.activo_dto import UpdateActivoDTO
from src.dtos.cuenta_dto import UpdateCuentaDTO
from src.dtos.inversor_dto import UpdateInversorDTO
from src.dtos.tenencia_dto import CreateTenenciaDTO
from src.routers.operacion_router import router as operacion_router
from src.services.activos_service import ActivoService
from src.services.cuenta_service import CuentaService
from src.services.inversor_service import InversorService
from src.services.tenencia_service import TenenciaService
from src.utils.errors import ConflictError


class IntegrityConflictTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.inversores = [
            Inversor(
                nombre=f"Inversor {suffix}",
                email=f"{suffix}@example.com",
                cuit=f"2012345678{index}",
                perfil_riesgo="agresivo",
            )
            for index, suffix in enumerate(("uno", "dos"), start=1)
        ]
        self.db.add_all(self.inversores)
        self.db.flush()

        self.cuentas = [
            Cuenta(
                inversor_id=inversor.id,
                numero_comitente=f"COM-{index}",
                saldo_ars=Decimal("10000"),
                saldo_usd=Decimal("0"),
            )
            for index, inversor in enumerate(self.inversores, start=1)
        ]
        self.activos = [
            Activo(
                ticker=f"ACT{index}",
                nombre=f"Activo {index}",
                tipo="accion",
                moneda="ARS",
                precio_actual=Decimal("10"),
                nivel_riesgo=1,
                activo=True,
            )
            for index in (1, 2)
        ]
        self.db.add_all(self.cuentas + self.activos)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_inversor_email_duplicado_devuelve_conflicto(self):
        with self.assertRaises(ConflictError):
            InversorService(self.db).update(
                self.inversores[0].id,
                UpdateInversorDTO(
                    nombre=None,
                    email=self.inversores[1].email,
                    cuit=None,
                    perfil_riesgo=None,
                ),
            )

        actual = self.db.get(Inversor, self.inversores[0].id)
        self.assertEqual(actual.email, "uno@example.com")

    def test_ticker_duplicado_devuelve_conflicto(self):
        with self.assertRaises(ConflictError):
            ActivoService(self.db).update(
                self.activos[0].id,
                UpdateActivoDTO(ticker=self.activos[1].ticker),
            )

        actual = self.db.get(Activo, self.activos[0].id)
        self.assertEqual(actual.ticker, "ACT1")

    def test_numero_comitente_duplicado_devuelve_conflicto(self):
        with self.assertRaises(ConflictError):
            CuentaService(self.db).update(
                self.cuentas[0].id,
                UpdateCuentaDTO(
                    numero_comitente=self.cuentas[1].numero_comitente
                ),
            )

        actual = self.db.get(Cuenta, self.cuentas[0].id)
        self.assertEqual(actual.numero_comitente, "COM-1")

    def test_tenencia_duplicada_devuelve_conflicto(self):
        self.db.add(
            Tenencia(
                cuenta_id=self.cuentas[0].id,
                activo_id=self.activos[0].id,
                cantidad=Decimal("1"),
                precio_promedio=Decimal("10"),
            )
        )
        self.db.commit()

        with self.assertRaises(ConflictError):
            TenenciaService(self.db).create(
                CreateTenenciaDTO(
                    cuenta_id=self.cuentas[0].id,
                    activo_id=self.activos[0].id,
                    cantidad=Decimal("1"),
                    precio_promedio=Decimal("10"),
                )
            )

        self.assertEqual(
            self.db.query(Tenencia)
            .filter_by(
                cuenta_id=self.cuentas[0].id,
                activo_id=self.activos[0].id,
            )
            .count(),
            1,
        )

    def test_post_de_operaciones_declara_201(self):
        create_route = next(
            route
            for route in operacion_router.routes
            if isinstance(route, APIRoute)
            and route.path.endswith("/")
            and "POST" in route.methods
        )
        self.assertEqual(create_route.status_code, 201)


if __name__ == "__main__":
    unittest.main()
