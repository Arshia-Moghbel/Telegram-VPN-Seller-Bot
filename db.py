from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings


engine = create_async_engine(
    settings.database_url,
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