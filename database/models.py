from datetime import datetime

from sqlalchemy import BigInteger, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id")
    )

    price: Mapped[int] = mapped_column()

    from models.order_status import OrderStatus

    status: Mapped[str] = mapped_column(
        String(50),
        default=OrderStatus.PENDING_PAYMENT.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(
        back_populates="orders"
    )

    plan: Mapped["Plan"] = relationship(
        back_populates="orders"
    )

    receipt: Mapped["Receipt | None"] = relationship(
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    price: Mapped[int] = mapped_column()

    duration: Mapped[int] = mapped_column()
    
    traffic: Mapped[str] = mapped_column(
        String(50)
    )

    is_active: Mapped[bool] = mapped_column(
        default=True
    )


    orders: Mapped[list["Order"]] = relationship(
        back_populates="plan"
    )


# Receipt model
class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        unique=True
    )

    telegram_file_id: Mapped[str] = mapped_column(
        String(255)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    order: Mapped["Order"] = relationship(
        back_populates="receipt"
    )


__all__ = [
    "User",
    "Order",
    "Plan",
    "Receipt"
]