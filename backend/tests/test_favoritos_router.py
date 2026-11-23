import unittest
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.db.connection import Base
from src.db.models.activos_model import Activo
from src.db.models.inversor_model import Inversor
from src.routers.dashboard_router import market_assets
from src.routers.favoritos_router import (
    create_favorito,
    delete_favorito,
    get_favoritos_by_inversor,
)
from src.schemas.favoritos_schema import CreateFavoritoSchema


class FavoritosRouterTests(unittest.TestCase):
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
        self.other_investor = Inversor(
            nombre="Otro Inversor",
            email="otro@example.com",
            cuit="20987654321",
            perfil_riesgo="conservador",
            password_hash="hashed",
            password_fingerprint="fingerprint-otro",
        )
        self.asset = Activo(
            ticker="AAPL.US",
            nombre="Apple",
            tipo="accion",
            moneda="USD",
            precio_actual=Decimal("100.00"),
            variacion_porcentual=Decimal("0"),
            nivel_riesgo=3,
            activo=True,
        )
        self.db.add_all([self.investor, self.other_investor, self.asset])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_favorite_is_persisted_listed_and_deleted_for_owner(self):
        payload = CreateFavoritoSchema(
            inversor_id=self.investor.id,
            activo_id=self.asset.id,
        )

        created = create_favorito(payload, self.db, self.investor)
        listed = get_favoritos_by_inversor(self.investor.id, self.db, self.investor)

        self.assertEqual(created.activo_id, self.asset.id)
        self.assertEqual([favorite.activo_id for favorite in listed], [self.asset.id])

        delete_favorito(self.investor.id, self.asset.id, self.db, self.investor)
        self.assertEqual(
            get_favoritos_by_inversor(self.investor.id, self.db, self.investor),
            [],
        )

    def test_favorites_are_private_to_the_authenticated_investor(self):
        with self.assertRaises(HTTPException) as context:
            get_favoritos_by_inversor(self.investor.id, self.db, self.other_investor)

        self.assertEqual(context.exception.status_code, 403)

    def test_market_assets_include_database_ids_for_favorite_mapping(self):
        assets = market_assets(self.db)

        self.assertEqual(assets[0]["id"], self.asset.id)


if __name__ == "__main__":
    unittest.main()
