"""
Database configuration and session management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ephemeris:ephemeris@localhost:5432/ephemeris_db"
)

# Convert to async URL for asyncpg
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Sync engine (for migrations)
sync_engine = create_engine(DATABASE_URL, echo=False)

# Async engine (for API)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Session factories
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database tables (sync, for startup)."""
    from . import db_models  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)
