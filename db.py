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
        await conn.run_sync(_migrate_schema)


def _migrate_schema(connection):
    columns = {
        column["name"]
        for column in connection.dialect.get_columns(connection, "plans")
    }

    if "description" not in columns:
        connection.exec_driver_sql(
            "ALTER TABLE plans ADD COLUMN description VARCHAR(500)"
        )
