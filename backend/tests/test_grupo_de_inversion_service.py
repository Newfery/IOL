import unittest
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.connection import Base
from src.db.models.grupo_de_inversion_model import GrupoDeInversion
from src.db.models.inversor_model import Inversor
from src.dtos.grupo_de_inversion_dto import (
    CreateGrupoDeInversionDTO,
    UpdateGrupoDeInversionDTO,
)
from src.services.grupo_de_inversion_service import GrupoDeInversionService
from src.utils.errors import ConflictError


class GrupoDeInversionServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.inversor = Inversor(
            nombre="Creador",
            email="creador@example.com",
            cuit="20123456789",
            perfil_riesgo="moderado",
        )
        self.db.add(self.inversor)
        self.db.commit()
        self.service = GrupoDeInversionService(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_create_get_update_and_delete(self):
        created = self.service.create(
            CreateGrupoDeInversionDTO(
                nombre="Grupo Uno",
                codigo_union="UNION-1",
                creador_id=self.inversor.id,
                plata_disponible=Decimal("1000"),
            )
        )

        self.assertEqual(created.nombre, "Grupo Uno")
        self.assertEqual(created.plata_disponible, Decimal("1000"))
        self.assertIsNotNone(self.service.get_by_id(created.id))

        updated = self.service.update(
            created.id,
            UpdateGrupoDeInversionDTO(plata_disponible=Decimal("750")),
        )
        self.assertEqual(updated.plata_disponible, Decimal("750"))
        self.assertTrue(self.service.delete(created.id))
        self.assertIsNone(self.service.get_by_id(created.id))

    def test_duplicate_codigo_devuelve_conflicto(self):
        dto = CreateGrupoDeInversionDTO(
            nombre="Grupo Uno",
            codigo_union="UNION-1",
            creador_id=self.inversor.id,
        )
        self.service.create(dto)

        with self.assertRaises(ConflictError):
            self.service.create(
                CreateGrupoDeInversionDTO(
                    nombre="Grupo Dos",
                    codigo_union="UNION-1",
                    creador_id=self.inversor.id,
                )
            )

        self.assertEqual(
            self.db.query(GrupoDeInversion).count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
