import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.settings import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middlewares
from app.cache.redis import get_redis, close_redis
from app.core.emby import emby
from app.core.seed import seed_data
from app.core.risk_monitor import start_risk_monitor
from app.db.session import AsyncSessionFactory

from app.modules.auth.api import router as auth_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.stats.api import router as stats_router, analytics_router
from app.modules.users.api import router as users_router, admin_router as users_admin_router
from app.modules.risk.api import router as risk_router
from app.modules.notifications.api import router as notifications_router
from app.modules.tasks.api import router as tasks_router
from app.modules.poster.api import router as poster_router
from app.modules.system.api import router as system_router
from app.modules.webhook.api import router as webhook_router
from app.modules.invites.api import router as invites_router
from app.modules.templates.api import router as templates_router
from app.modules.portal.api import router as portal_router
from app.modules.media.api import router as media_router
from app.modules.calendar.api import router as calendar_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await get_redis()
    await seed_data()
    start_risk_monitor(AsyncSessionFactory)
    logger.info("🛡️ Risk monitor started")
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
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(users_admin_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(poster_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(webhook_router, prefix=API_PREFIX)
app.include_router(invites_router, prefix=API_PREFIX)
app.include_router(templates_router, prefix=API_PREFIX)
app.include_router(portal_router, prefix=API_PREFIX)
app.include_router(media_router, prefix=API_PREFIX)
app.include_router(calendar_router, prefix=API_PREFIX)


@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok"}
