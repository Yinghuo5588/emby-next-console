import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.settings import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middlewares
from app.cache.redis import get_redis, close_redis
from app.core.emby import emby
from app.db.session import AsyncSessionFactory

# 仅保留可用模块
from app.modules.auth.api import router as auth_router
from app.modules.stats.api import router as stats_router
from app.modules.media.proxy import router as proxy_router
from app.modules.system.api import router as system_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.users.api import router as users_router

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
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(proxy_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)


@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok"}
