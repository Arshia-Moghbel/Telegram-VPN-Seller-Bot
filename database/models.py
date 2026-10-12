from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
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

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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

    discount_amount: Mapped[int] = mapped_column(default=0, nullable=False)

    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

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

    duration: Mapped[float] = mapped_column(Float)

    duration_unit: Mapped[str] = mapped_column(
        String(10),
        default="month",
        nullable=False,
    )
    
    traffic: Mapped[str] = mapped_column(
        String(50)
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        default=True
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    value: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(10))
    value: Mapped[int] = mapped_column()
    max_uses: Mapped[int | None] = mapped_column(nullable=True)
    uses_count: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    __table_args__ = (UniqueConstraint("coupon_id", "user_id", name="uq_coupon_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


__all__ = [
    "User",
    "Order",
    "Plan",
    "Receipt",
    "AdminSetting",
    "Coupon",
    "CouponRedemption",
]
