"""
PostgreSQL Database Configuration for Rafiki.ai
Uses SQLAlchemy with async support for production-ready database operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
import os
from typing import AsyncGenerator

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


# Database URL from environment variable
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/rafiki"
)

# Handle Render's postgres:// URL format (needs postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",  # SQL logging in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,  # Connection pool size
    max_overflow=10,  # Allow up to 10 additional connections
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from backend.models.db_models import User, OTPRecord, Session, Conversation, Message, AuditLog
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    print("✅ Database connections closed")
