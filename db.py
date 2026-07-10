from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase


DATABASE_URL = "sqlite+aiosqlite:///vpnifi.db"


engine = create_async_engine(
    DATABASE_URL,
    echo=False
)


async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with async_session() as session:
        yield session


async def create_db():
    from database import models
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)