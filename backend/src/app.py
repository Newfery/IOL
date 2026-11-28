import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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
from src.db.seeders.yfinance_assets import sync_assets as sync_yfinance_assets
from src.services.data912_service import Data912ProviderError, sync_data912_assets
from src.services.finnhub_service import FinnhubProviderError, sync_finnhub_assets
from src.utils.errors import AppError

logger = logging.getLogger(__name__)
DATA912_REFRESH_SECONDS = 2 * 60 * 60
FINNHUB_REFRESH_SECONDS = 6 * 60 * 60
FINNHUB_RETRY_SECONDS = 60


async def _refresh_data912_periodically(startup_task: asyncio.Task[None]) -> None:
    await asyncio.wait((startup_task,))

    while True:
        try:
            updated, missing = await asyncio.to_thread(sync_data912_assets)
            logger.info(
                "Sincronización Data912: %s activos actualizados, %s tickers no registrados",
                updated,
                missing,
            )
        except (Data912ProviderError, SQLAlchemyError):
            logger.exception("Falló la actualización de precios desde Data912")
        await asyncio.sleep(DATA912_REFRESH_SECONDS)


async def _refresh_finnhub_periodically() -> None:
    while True:
        try:
            inserted, updated = await asyncio.to_thread(sync_finnhub_assets)
            logger.info(
                "Sincronización Finnhub: %s nuevos, %s actualizados",
                inserted,
                updated,
            )
        except (FinnhubProviderError, SQLAlchemyError):
            logger.exception("Falló la actualización de activos desde Finnhub")
            await asyncio.sleep(FINNHUB_RETRY_SECONDS)
            continue
        if inserted == 0:
            logger.info(
                "Finnhub no encontró activos nuevos con cotización disponible; "
                "se volverá a intentar en %s horas",
                FINNHUB_REFRESH_SECONDS // 3600,
            )
            await asyncio.sleep(FINNHUB_REFRESH_SECONDS)


async def _sync_yahoo_assets_on_startup() -> None:
    inserted, updated, skipped, validated_us_equities = await asyncio.to_thread(
        sync_yfinance_assets
    )
    logger.info(
        "Sincronización inicial de Yahoo Finance: %s nuevos, %s actualizados, "
        "%s acciones de EE. UU. validadas y %s símbolos omitidos",
        inserted,
        updated,
        validated_us_equities,
        len(skipped),
    )


def _log_yahoo_sync_failure(task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error(
            "Falló la sincronización inicial de Yahoo Finance; "
            "continúa la actualización de precios de Data912",
            exc_info=(type(error), error, error.__traceback__),
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    yahoo_task = asyncio.create_task(_sync_yahoo_assets_on_startup())
    yahoo_task.add_done_callback(_log_yahoo_sync_failure)
    data912_task = asyncio.create_task(_refresh_data912_periodically(yahoo_task))
    finnhub_task = asyncio.create_task(_refresh_finnhub_periodically())
    try:
        yield
    finally:
        tasks = (yahoo_task, data912_task, finnhub_task)
        for task in tasks:
            if not task.done():
                task.cancel()
        for task in tasks:
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
