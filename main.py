"""FastAPI application entry point.

This module is the sole entry point for the authentication service.
It contains only:
  - Lifespan handler (DB pool startup / shutdown)
  - Application initialisation
  - Router registration
  - Global exception handler registration

No business logic, no route logic, no direct database access here.

Run with:
  uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.database.connection import engine
from src.routes.auth import router as auth_router
from src.routes.default import router as default_router
from src.services.dependencies import ServiceContainer
from src.settings import settings
from src.utils.constants import MSG_INTERNAL_ERROR
from src.utils.exceptions import AppError
from src.utils.logger import logger


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Startup:
      - Calls ServiceContainer.initialise() which creates the app-scoped
        PasswordHasher and JWTHandler singleton instances once, before
        the first request is served.
      - Warms up the SQLAlchemy async connection pool.

    Shutdown:
      - Disposes all pooled DB connections cleanly.
    """
    # Initialise all app-scoped service singletons
    logger.info("Startup — initialising service container")
    ServiceContainer.initialise()

    # Warm up the DB connection pool
    logger.info("Startup — warming database connection pool")
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)
    logger.info("Startup complete")

    yield  # application serves requests here

    logger.info("Shutdown — disposing database connection pool")
    await engine.dispose()
    logger.info("Shutdown complete")


# ── Application ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade user authentication service with JWT and bcrypt.",
    lifespan=lifespan,
)

# ── Router registration ───────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(default_router)


# ── Global exception handlers ─────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Returns HTTP 400 when all errors are missing-field errors.
    Returns HTTP 422 for all other validation failures.
    All field errors are accumulated into a single response.
    """
    errors = exc.errors()
    all_missing = all(e.get("type") == "missing" for e in errors)
    status_code = 400 if all_missing else 422
    messages = [e.get("msg", "Validation error") for e in errors]
    return JSONResponse(
        status_code=status_code,
        content={"status_code": status_code, "message": "; ".join(messages)},
    )


@app.exception_handler(AppError)
async def app_exception_handler(
    request: Request, exc: AppError
) -> JSONResponse:
    """Map domain-level AppError subclasses to structured JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "message": exc.message},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Pass HTTPException through with a consistent JSON body structure."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "message": detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for any unhandled exception.

    Logs the full stack trace at ERROR level and returns a sanitised
    500 response — no internal details exposed to the caller.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"status_code": 500, "message": MSG_INTERNAL_ERROR},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
