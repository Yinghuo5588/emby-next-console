import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.settings import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middlewares
from app.cache.redis import get_redis, close_redis
from app.core.emby import emby

from app.modules.auth.api import router as auth_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.stats.api import router as stats_router
from app.modules.users.api import router as users_router
from app.modules.risk.api import router as risk_router
from app.modules.notifications.api import router as notifications_router
from app.modules.system.api import router as system_router
from app.modules.webhook.api import router as webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await get_redis()
    yield
    logger.info("Shutting down...")
    await emby.close()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

register_middlewares(app)
register_exception_handlers(app)

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(webhook_router, prefix=API_PREFIX)


@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok"}
