from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings
import os
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows does not support flock.
    fcntl = None


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


_instance_lock_fd: int | None = None


def acquire_instance_lock() -> None:
    """Prevent two polling processes from consuming the same updates on one host."""
    global _instance_lock_fd
    if _instance_lock_fd is not None or fcntl is None:
        return

    lock_path = Path(settings.instance_lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        os.close(fd)
        raise RuntimeError(
            "Another bot process is already running (instance lock is held)."
        ) from error
    _instance_lock_fd = fd


def release_instance_lock() -> None:
    global _instance_lock_fd
    if _instance_lock_fd is None:
        return
    if fcntl is not None:
        fcntl.flock(_instance_lock_fd, fcntl.LOCK_UN)
    os.close(_instance_lock_fd)
    _instance_lock_fd = None


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
    if "duration_unit" not in plan_columns:
        connection.exec_driver_sql(
            "ALTER TABLE plans ADD COLUMN duration_unit VARCHAR(10) NOT NULL DEFAULT 'month'"
        )

    order_columns = {
        column["name"] for column in connection.dialect.get_columns(connection, "orders")
    }
    if "discount_amount" not in order_columns:
        connection.exec_driver_sql(
            "ALTER TABLE orders ADD COLUMN discount_amount INTEGER NOT NULL DEFAULT 0"
        )
    if "coupon_code" not in order_columns:
        connection.exec_driver_sql("ALTER TABLE orders ADD COLUMN coupon_code VARCHAR(50)")

    duration_column = next(
        (column for column in connection.dialect.get_columns(connection, "plans") if column["name"] == "duration"),
        None,
    )
    if (
        connection.dialect.name == "postgresql"
        and duration_column is not None
        and "integer" in str(duration_column["type"]).lower()
    ):
        connection.exec_driver_sql(
            "ALTER TABLE plans ALTER COLUMN duration TYPE DOUBLE PRECISION "
            "USING duration::double precision"
        )

    user_columns = {
        column["name"] for column in connection.dialect.get_columns(connection, "users")
    }
    if "is_blocked" not in user_columns:
        connection.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN is_blocked BOOLEAN NOT NULL DEFAULT 0"
        )
