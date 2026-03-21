import time
import logging

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.core.settings import settings

logger = logging.getLogger("app.request")


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"{request.method} {request.url.path} {response.status_code} {elapsed:.1f}ms")
        return response
