# Importaciones
from src.db.models.operacion_model import Operacion
from src.dtos.operacion_dto import OperacionCreate, OperacionResponse


class OperacionMapper:

    # Convierte un DTO de creación en un modelo Operacion
    @staticmethod
    def to_model(dto: OperacionCreate):

        operacion = Operacion(
            cuenta_id=dto.cuenta_id,
            activo_id=dto.activo_id,
            tipo=dto.tipo,
            cantidad=dto.cantidad,
            precio_unitario=dto.precio_unitario,
            comision=dto.comision,
            total=dto.total,
            estado=dto.estado
        )

        return operacion

    # Convierte un modelo Operacion en un DTO de respuesta
    @staticmethod
    def to_dto(operacion: Operacion):

        dto = OperacionResponse.model_validate(operacion)

        return dto

    # Convierte una lista de operaciones en una lista de DTOs
    @staticmethod
    def to_dto_list(operaciones: list[Operacion]):

        lista_dto = []

        for operacion in operaciones:
            dto = OperacionMapper.to_dto(operacion)
            lista_dto.append(dto)

        return lista_dto