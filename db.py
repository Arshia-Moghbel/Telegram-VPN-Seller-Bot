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
    plan_columns = {
        column["name"] for column in connection.dialect.get_columns(connection, "plans")
    }

    if "description" not in plan_columns:
        connection.exec_driver_sql(
            "ALTER TABLE plans ADD COLUMN description VARCHAR(500)"
        )
    if "is_deleted" not in plan_columns:
        connection.exec_driver_sql(
            "ALTER TABLE plans ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0"
        )

    user_columns = {
        column["name"] for column in connection.dialect.get_columns(connection, "users")
    }
    if "is_blocked" not in user_columns:
        connection.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN is_blocked BOOLEAN NOT NULL DEFAULT 0"
        )
