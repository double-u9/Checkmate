"""Database session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


_db_url = get_settings().database_url
_is_sqlite = "sqlite" in _db_url

_engine_kwargs = {
    "echo": get_settings().debug,
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10

engine = create_async_engine(_db_url, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency that yields a database session.
    
    Routes are responsible for calling commit() explicitly when they
    perform write operations. Read-only routes do not trigger wasteful commits.
    On exception, the session is rolled back automatically.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
