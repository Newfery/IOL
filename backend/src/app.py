import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError

from src.middlewares.error_middleware import app_error_handler
from src.config.env import settings
from src.routers import (
    activos_router,
    auth_router,
    cuenta_router,
    dashboard_router,
    dividendo_router,
    favoritos_router,
    grupo_de_inversion_router,
    grupo_inversor_router,
    inversor_router,
    movimiento_router,
    operacion_router,
    tenencia_router,
)
from src.utils.errors import AppError
from src.services.cafci_service import CafciProviderError, sync_cafci_assets

logger = logging.getLogger(__name__)
CAFCI_REFRESH_SECONDS = 6 * 60 * 60


async def _refresh_cafci_periodically() -> None:
    while True:
        try:
            inserted, updated = await asyncio.to_thread(sync_cafci_assets)
            logger.info("Sincronización CAFCI: %s nuevos, %s actualizados", inserted, updated)
        except (CafciProviderError, SQLAlchemyError):
            logger.exception("Falló la actualización de cuotapartes CAFCI")
        await asyncio.sleep(CAFCI_REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_refresh_cafci_periodically())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Initial Structure API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon_path = Path(__file__).parent / "static" / "favicon.ico"
    return FileResponse(icon_path, media_type="image/x-icon")


app.add_exception_handler(AppError, app_error_handler)

app.include_router(inversor_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(cuenta_router.router, prefix="/api")
app.include_router(dashboard_router.router, prefix="/api")
app.include_router(activos_router.router, prefix="/api")
app.include_router(operacion_router.router, prefix="/api")
app.include_router(dividendo_router.router, prefix="/api")
app.include_router(movimiento_router.router, prefix="/api")
app.include_router(tenencia_router.router, prefix="/api")
app.include_router(favoritos_router.router, prefix="/api")
app.include_router(grupo_de_inversion_router.router, prefix="/api")
app.include_router(grupo_inversor_router.router, prefix="/api")
# TODO: registrar product_router cuando se implemente
# app.include_router(product_router.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
