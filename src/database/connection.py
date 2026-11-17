"""Async SQLAlchemy engine and session factory.

The engine and session factory are module-level singletons created once
at import time. The lifespan handler in main.py connects the pool on
startup and disposes it on shutdown.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings import settings

# Async engine — pool_pre_ping detects stale connections before use
engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Session factory — expire_on_commit=False keeps objects usable after commit
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
