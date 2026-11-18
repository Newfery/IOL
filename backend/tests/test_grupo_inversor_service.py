import unittest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.connection import Base
from src.db.models.grupo_inversor_model import GrupoInversor
from src.db.models.inversor_model import Inversor
from src.dtos.grupo_de_inversion_dto import CreateGrupoDeInversionDTO
from src.dtos.grupo_inversor_dto import CreateGrupoInversorDTO
from src.services.grupo_de_inversion_service import GrupoDeInversionService
from src.services.grupo_inversor_service import GrupoInversorService
from src.utils.errors import ConflictError, NotFoundError


class GrupoInversorServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.lider = self.crear_inversor("Lider", "20123456789")
        self.integrante = self.crear_inversor("Integrante", "20987654321")
        self.grupo = GrupoDeInversionService(self.db).create(
            CreateGrupoDeInversionDTO(
                nombre="Grupo Uno",
                codigo_union="UNION-1",
                creador_id=self.lider.id,
                plata_disponible=Decimal("100"),
            )
        )
        self.service = GrupoInversorService(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def crear_inversor(self, nombre: str, cuit: str) -> Inversor:
        inversor = Inversor(
            nombre=nombre,
            email=f"{nombre.lower()}@example.com",
            cuit=cuit,
            perfil_riesgo="moderado",
            password_hash="hashed-password",
            password_fingerprint=f"fingerprint-{nombre.lower()}",
        )
        self.db.add(inversor)
        self.db.commit()
        return inversor

    def test_creador_es_integrante_y_se_puede_agregar_con_fecha(self):
        fecha_union = datetime(2026, 3, 10, 12, 30)

        creado = self.service.create(
            CreateGrupoInversorDTO(
                grupo_id=self.grupo.id,
                inversor_id=self.integrante.id,
                fecha_union=fecha_union,
            )
        )

        integrantes = self.service.get_by_grupo(self.grupo.id)
        integrantes_por_id = {
            integrante.inversor_id: integrante
            for integrante in integrantes
        }
        self.assertIn(self.lider.id, integrantes_por_id)
        self.assertEqual(creado.fecha_union, fecha_union)
        self.assertEqual(integrantes_por_id[self.integrante.id].fecha_union, fecha_union)
        self.assertEqual(self.db.query(GrupoInversor).count(), 2)

    def test_rechaza_duplicados_y_no_elimina_al_lider(self):
        with self.assertRaises(ConflictError):
            self.service.create(
                CreateGrupoInversorDTO(
                    grupo_id=self.grupo.id,
                    inversor_id=self.lider.id,
                )
            )
        with self.assertRaises(ConflictError):
            self.service.delete(self.grupo.id, self.lider.id)

    def test_rechaza_grupo_o_inversor_inexistente(self):
        with self.assertRaises(NotFoundError):
            self.service.create(
                CreateGrupoInversorDTO(
                    grupo_id=999,
                    inversor_id=self.integrante.id,
                )
            )
        with self.assertRaises(NotFoundError):
            self.service.create(
                CreateGrupoInversorDTO(
                    grupo_id=self.grupo.id,
                    inversor_id=999,
                )
            )


if __name__ == "__main__":
    unittest.main()
