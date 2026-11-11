from fastapi import FastAPI

from src.middlewares.error_middleware import app_error_handler
from src.routers import (
    inversor_router,
    cuenta_router,
    activo_router,
    operacion_router,
    movimiento_router,
    dividiendo_router,  
)
from src.utils.errors import AppError

app = FastAPI(title="Initial Structure API")

app.add_exception_handler(AppError, app_error_handler)

app.include_router(inversor_router.router, prefix="/api")
app.include_router(cuenta_router.router, prefix="/api")
app.include_router(activo_router.router, prefix="/api")
app.include_router(operacion_router.router, prefix="/api")
app.include_router(movimiento_router.router, prefix="/api")
app.include_router(dividiendo_router.router, prefix="/api")
# TODO: registrar product_router cuando se implemente
# app.include_router(product_router.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
