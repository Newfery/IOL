import unittest
from decimal import Decimal
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.db.connection import Base
from src.db.models.activos_model import Activo
from src.db.models.aporte_grupo_model import AporteGrupo
from src.db.models.cuenta_model import Cuenta
from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.grupo_inversor_model import GrupoInversor
from src.db.models.inversor_model import Inversor
from src.routers.dashboard_router import contribute_group
from src.schemas.frontend_schema import GroupContributionRequest
from src.services.dolar_service import DolarQuoteError


class GroupContributionRouteTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.investor = Inversor(
            nombre="Inversor Demo",
            email="demo@example.com",
            cuit="20123456789",
            perfil_riesgo="moderado",
            password_hash="hashed",
            password_fingerprint="fingerprint-demo",
        )
        self.db.add(self.investor)
        self.db.flush()
        self.account = Cuenta(
            inversor_id=self.investor.id,
            numero_comitente="COMITENTE-1",
            saldo_ars=Decimal("1000.00"),
            saldo_usd=Decimal("100.00"),
        )
        self.group = GrupoDeInversion(
            nombre="Grupo Demo",
            codigo_union="DEMO1",
            creador_id=self.investor.id,
            password_hash="hashed",
            plata_disponible=Decimal("50.00"),
        )
        self.db.add_all([self.account, self.group])
        self.db.flush()
        self.investor_id = getattr(self.investor, "id")
        self.group_id = getattr(self.group, "id")
        self.db.add(
            GrupoInversor(grupo_id=self.group_id, inversor_id=self.investor_id)
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    @patch("src.routers.dashboard_router.OperacionService.acreditar_liquidaciones_vencidas")
    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_usd_contribution_debits_usd_and_credits_ars_at_mep(
        self,
        quote_mock,
        _settlement_mock,
    ):
        quote_mock.return_value = Decimal("1500.25")

        response = contribute_group(
            self.group_id,
            GroupContributionRequest(monto=Decimal("10.00"), moneda="USD"),
            self.db,
            self.investor,
        )

        self.assertEqual(response["cash"], 15052.5)
        self.assertEqual(response["members"][0]["contributed"], 15002.5)
        self.assertEqual(response["members"][0]["contributedUsd"], 10)
        self.db.refresh(self.account)
        self.assertEqual(self.account.saldo_usd, Decimal("90.00"))
        self.assertEqual(self.account.saldo_ars, Decimal("1000.00"))
        contribution = self.db.query(AporteGrupo).one()
        self.assertEqual(contribution.moneda, "USD")
        self.assertEqual(contribution.monto_original, Decimal("10.00"))
        self.assertEqual(contribution.cotizacion_mep, Decimal("1500.2500"))
        quote_mock.assert_called_once_with("mep")
        _settlement_mock.assert_called_once_with(self.db, self.account)

    @patch("src.routers.dashboard_router.OperacionService.acreditar_liquidaciones_vencidas")
    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_ars_contribution_remains_the_default(
        self,
        quote_mock,
        _settlement_mock,
    ):
        response = contribute_group(
            self.group_id,
            GroupContributionRequest(monto=Decimal("25.00")),
            self.db,
            self.investor,
        )

        self.assertEqual(response["cash"], 75)
        self.assertEqual(response["members"][0]["contributed"], 25)
        self.assertEqual(response["members"][0]["contributedUsd"], 0)
        self.db.refresh(self.account)
        self.assertEqual(self.account.saldo_ars, Decimal("975.00"))
        contribution = self.db.query(AporteGrupo).one()
        self.assertEqual(contribution.moneda, "ARS")
        self.assertEqual(contribution.cotizacion_mep, None)
        quote_mock.assert_not_called()
        _settlement_mock.assert_called_once_with(self.db, self.account)

    @patch("src.routers.dashboard_router.OperacionService.acreditar_liquidaciones_vencidas")
    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_usd_contribution_fails_without_mep_without_changing_balances(
        self,
        quote_mock,
        _settlement_mock,
    ):
        quote_mock.side_effect = DolarQuoteError("offline")

        with self.assertRaises(HTTPException) as context:
            contribute_group(
                self.group_id,
                GroupContributionRequest(monto=Decimal("10.00"), moneda="USD"),
                self.db,
                self.investor,
            )

        self.assertEqual(context.exception.status_code, 503)
        self.db.refresh(self.account)
        self.db.refresh(self.group)
        self.assertEqual(self.account.saldo_usd, Decimal("100.00"))
        self.assertEqual(self.group.plata_disponible, Decimal("50.00"))
        self.assertEqual(self.db.query(AporteGrupo).count(), 0)
        _settlement_mock.assert_called_once_with(self.db, self.account)

    @patch("src.routers.dashboard_router.OperacionService.acreditar_liquidaciones_vencidas")
    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_usd_contribution_uses_local_bond_quotes_before_external_mep(
        self,
        quote_mock,
        _settlement_mock,
    ):
        self.db.add_all(
            [
                Activo(
                    ticker="AL30",
                    nombre="AL30",
                    tipo="bono",
                    moneda="ARS",
                    precio_actual=Decimal("1000"),
                    variacion_porcentual=Decimal("0"),
                    nivel_riesgo=1,
                    activo=True,
                ),
                Activo(
                    ticker="AL30D",
                    nombre="AL30D",
                    tipo="bono",
                    moneda="USD",
                    precio_actual=Decimal("1"),
                    variacion_porcentual=Decimal("0"),
                    nivel_riesgo=1,
                    activo=True,
                ),
            ]
        )
        self.db.commit()

        result = contribute_group(
            self.group_id,
            GroupContributionRequest(monto=Decimal("1.00"), moneda="USD"),
            self.db,
            self.investor,
        )

        self.assertEqual(result["cash"], 1050)
        contribution = self.db.query(AporteGrupo).one()
        self.assertEqual(contribution.cotizacion_mep, Decimal("1000.0000"))
        quote_mock.assert_not_called()
        _settlement_mock.assert_called_once_with(self.db, self.account)

    @patch("src.routers.dashboard_router.OperacionService.acreditar_liquidaciones_vencidas")
    @patch("src.routers.dashboard_router.DolarQuoteService.obtener")
    def test_rejects_usd_contribution_over_available_usd_balance(
        self,
        quote_mock,
        _settlement_mock,
    ):
        setattr(self.account, "saldo_usd", Decimal("5.00"))
        self.db.commit()

        with self.assertRaises(HTTPException) as context:
            contribute_group(
                self.group_id,
                GroupContributionRequest(monto=Decimal("10.00"), moneda="USD"),
                self.db,
                self.investor,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.db.refresh(self.account)
        self.assertEqual(self.account.saldo_usd, Decimal("5.00"))
        self.assertEqual(self.db.query(AporteGrupo).count(), 0)
        quote_mock.assert_not_called()
        _settlement_mock.assert_called_once_with(self.db, self.account)


if __name__ == "__main__":
    unittest.main()
