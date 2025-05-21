from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.pool import QueuePool
import contextlib
from typing import AsyncGenerator

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info(f"Loaded DB URL: {settings.DATABASE_URL}")

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Get a database connection from the engine pool.
    
    Yields:
        An async database connection object
    """
    async with engine.connect() as connection:
        logger.debug("Database connection acquired")
        try:
            yield connection
        finally:
            logger.debug("Database connection released")

@contextlib.asynccontextmanager
async def get_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Context manager for getting a database connection.
    
    Yields:
        An async database connection
    """
    async with engine.connect() as connection:
        logger.debug("Database connection acquired (context manager)")
        try:
            yield connection
        finally:
            logger.debug("Database connection released (context manager)")
