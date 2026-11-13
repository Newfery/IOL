from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.middlewares.error_middleware import app_error_handler
from src.routers import (
    activos_router,
    cuenta_router,
    dividendo_router,
    favoritos_router,
    inversor_router,
    movimiento_router,
    operacion_router,
    tenencia_router,
)
from src.utils.errors import AppError

app = FastAPI(title="Initial Structure API")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon_path = Path(__file__).parent / "static" / "favicon.ico"
    return FileResponse(icon_path, media_type="image/x-icon")


app.add_exception_handler(AppError, app_error_handler)

app.include_router(inversor_router.router, prefix="/api")
app.include_router(cuenta_router.router, prefix="/api")
app.include_router(activos_router.router, prefix="/api")
app.include_router(operacion_router.router, prefix="/api")
app.include_router(dividendo_router.router, prefix="/api")
app.include_router(movimiento_router.router, prefix="/api")
app.include_router(tenencia_router.router, prefix="/api")
app.include_router(favoritos_router.router, prefix="/api")
# TODO: registrar product_router cuando se implemente
# app.include_router(product_router.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
