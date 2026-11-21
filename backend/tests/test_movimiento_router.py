import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

from fastapi import HTTPException

from src.db.models.inversor_model import Inversor
from src.routers.movimiento_router import create_movimiento
from src.schemas.movimiento_schema import CreateMovimientoSchema


class CreateMovimientoRouteTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.query.return_value.filter.return_value.scalar.return_value = 12
        self.current = Inversor(id=5)
        self.payload = CreateMovimientoSchema(
            cuenta_id=12,
            tipo="deposito",
            moneda="ARS",
            monto=Decimal("100"),
        )

    @patch("src.routers.movimiento_router.MovimientoService")
    def test_creates_movement_for_authenticated_investor_account(self, service_mock):
        create_movimiento(self.payload, self.db, self.current)

        service_mock.assert_called_once_with(self.db)
        service_mock.return_value.create.assert_called_once()

    @patch("src.routers.movimiento_router.MovimientoService")
    def test_rejects_movement_for_another_account(self, service_mock):
        self.payload.cuenta_id = 99

        with self.assertRaises(HTTPException) as context:
            create_movimiento(self.payload, self.db, self.current)

        self.assertEqual(context.exception.status_code, 403)
        service_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
