"""Dependency injection wiring for the authentication service.

This module defines a ServiceContainer singleton that holds all
app-scoped instances (PasswordHasher, JWTHandler). The container is
initialised once during application startup via the lifespan handler
in main.py.

Usage in main.py lifespan:
    ServiceContainer.initialise()

Usage in routes:
    service: AuthService = Depends(get_auth_service)

Dependency chain per request:
    get_db_session()              → AsyncSession (request-scoped)
        └── get_user_repository() → UserRepository (request-scoped)
                └── get_auth_service() → AuthService (request-scoped,
                                         uses app-scoped singletons
                                         from ServiceContainer)
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import AsyncSessionFactory
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.utils.jwt_handler import JWTHandler
from src.utils.password import PasswordHasher


class ServiceContainer:
    """Singleton container for all app-scoped service instances.

    Guarantees that PasswordHasher and JWTHandler are created exactly
    once for the lifetime of the application, regardless of how many
    requests are handled concurrently.

    Call ServiceContainer.initialise() in the lifespan handler to
    create the instances before the first request arrives.
    """

    _instance: "ServiceContainer | None" = None

    def __new__(cls) -> "ServiceContainer":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._password_hasher = PasswordHasher()
            cls._instance._jwt_handler = JWTHandler()
        return cls._instance

    @classmethod
    def initialise(cls) -> "ServiceContainer":
        """Create and return the singleton container.

        Calling this explicitly in the lifespan startup ensures the
        instances are ready before any request is served.
        """
        return cls()

    @property
    def password_hasher(self) -> PasswordHasher:
        return self._password_hasher

    @property
    def jwt_handler(self) -> JWTHandler:
        return self._jwt_handler


# ── Request-scoped dependency functions ──────────────────────────────

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the duration of a single request."""
    async with AsyncSessionFactory() as session:
        yield session


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Provide a UserRepository bound to the current request's session."""
    return UserRepository(session)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provide an AuthService using app-scoped singletons from ServiceContainer."""
    container = ServiceContainer()
    return AuthService(
        repo=repo,
        hasher=container.password_hasher,
        jwt_handler=container.jwt_handler,
    )
