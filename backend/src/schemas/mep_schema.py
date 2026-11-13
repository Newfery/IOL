from decimal import Decimal

from pydantic import BaseModel, Field


class MEPRequestSchema(BaseModel):
    monto_ars: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
