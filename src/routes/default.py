"""Baseline application endpoints for infrastructure health checks.

Provides:
  GET /       — returns API name and version (no DB call)
  GET /health — liveness probe (no DB call)
  GET /ready  — readiness probe (DB connection check with 5-second timeout)
"""

import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from src.database.connection import AsyncSessionFactory
from src.settings import settings
from src.utils.constants import DB_READY_TIMEOUT_SECONDS

router = APIRouter(tags=["Health"])


@router.get("/")
async def root() -> dict:
    """Return API name and version. No database call."""
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/health")
async def health() -> dict:
    """Liveness check — confirms the process is running. No database call."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    """Readiness check — probes the database with a 5-second timeout.

    Returns HTTP 200 if the DB responds within DB_READY_TIMEOUT_SECONDS.
    Returns HTTP 503 if the DB times out or raises an error.
    """
    from fastapi import HTTPException

    try:
        async def _probe() -> None:
            async with AsyncSessionFactory() as session:
                await session.execute(text("SELECT 1"))

        await asyncio.wait_for(_probe(), timeout=DB_READY_TIMEOUT_SECONDS)
        return {"status": "ready"}
    except (TimeoutError, Exception):
        raise HTTPException(status_code=503, detail={"status": "unavailable"})
