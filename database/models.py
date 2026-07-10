from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    plan: Mapped[str] = mapped_column(
        String(50)
    )

    price: Mapped[int] = mapped_column()

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )