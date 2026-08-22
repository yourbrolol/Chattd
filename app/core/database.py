"""
FastAPI Database Configuration with SQLAlchemy

This module sets up:
1. Async database connection (PostgreSQL, SQLite, etc.)
2. Session management for database operations
3. Base model class for ORM models
4. Dependency injection for FastAPI routes
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,           # Async session object - handles DB transactions
    create_async_engine,    # Creates async database engine
    async_sessionmaker,     # Factory to create async session instances
)
from sqlalchemy.orm import declarative_base  # Base class for all ORM models
from sqlalchemy.pool import StaticPool
from decouple import config  # Load environment variables
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE URL CONFIGURATION
# ============================================================================

# Get database URL from .env file
# For SQLite (development): "sqlite+aiosqlite:///./db.sqlite3"
# For PostgreSQL (production): "postgresql+asyncpg://user:password@localhost/dbname"
DATABASE_URL = config(
    "DATABASE_URL",
    default="sqlite+aiosqlite:///./app/db.sqlite3"  # Default to local SQLite
)

logger.info(f"Database URL: {DATABASE_URL}")

# ============================================================================
# CREATE ASYNC ENGINE
# ============================================================================

# The engine is the connection pool manager
# - "echo=True" prints all SQL queries (useful for debugging)
# - "pool_pre_ping=True" tests connections before using them (prevents stale connections)
# - "pool_recycle=3600" recycles connections every hour (prevents timeout issues)
engine = create_async_engine(
    DATABASE_URL,
    # Set SQL_ECHO=True to see queries
    echo=config("SQL_ECHO", default=False, cast=bool),
    pool_pre_ping=True,      # Check if connection is alive before using it
    pool_recycle=3600,       # Recycle connections after 1 hour to prevent timeouts
    future=True,             # Use SQLAlchemy 2.0 style (required for async)
    poolclass=StaticPool if "file:testmemdb" in DATABASE_URL else None,
)

# ============================================================================
# CREATE ASYNC SESSION FACTORY
# ============================================================================

# SessionLocal is a factory that creates new async session instances
# expire_on_commit=False: keeps model objects usable after commit (useful for API responses)
# class_=AsyncSession: use async session (allows await db.execute(), etc.)
SessionLocal = async_sessionmaker(
    bind=engine,                    # Bind to our async engine
    class_=AsyncSession,            # Use async session class
    expire_on_commit=False,         # Keep model objects valid after commit
    # Don't auto-flush before queries (more control)
    autoflush=False,
    autocommit=False,               # Explicit commit required
)

# ============================================================================
# DECLARATIVE BASE FOR MODELS
# ============================================================================

# All ORM models will inherit from this Base class
# When you do: class User(Base): ...
# SQLAlchemy knows it's an ORM model and will create the table mapping
Base = declarative_base()

# ============================================================================
# DEPENDENCY INJECTION FUNCTION
# ============================================================================


async def get_db() -> AsyncSession:
    """
    FastAPI dependency to inject a database session into route handlers.

    Usage in a route:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    This function:
    1. Creates a new session
    2. Yields it to the route handler
    3. Closes it after the route completes (cleanup)
    """
    async with SessionLocal() as session:
        try:
            yield session  # Give session to the route handler
        finally:
            await session.close()  # Cleanup: close the connection


# ============================================================================
# DATABASE INITIALIZATION (run on app startup)
# ============================================================================

async def init_db():
    """
    Creates all tables defined in your models.

    This should be called once on app startup.
    Alternative: Use Alembic for migrations (more robust for production)

    Usage in main.py:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    # Ensure all model modules are imported so their tables are registered
    # with SQLAlchemy's declarative `Base` before creating tables.
    try:
        # Local import to avoid top-level import side-effects / circular imports
        import importlib

        importlib.import_module("app.chat.models")
    except Exception:
        logger.exception("Failed to import app.chat.models before initializing DB")

    async with engine.begin() as conn:
        # Creates all tables defined by Base subclasses
        # Only creates tables that don't exist (safe to run multiple times)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def close_db():
    """
    Closes the database engine and connection pool.

    Should be called on app shutdown to clean up connections.

    Usage in main.py:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    await engine.dispose()  # Close all connections in the pool
    logger.info("Database connection pool closed")
