from datetime import datetime, timedelta

from sqlalchemy import func, select

from config import settings
from database.models import AdminSetting, Order, User
from db import async_session
from models.order_status import OrderStatus


PAYMENT_SETTING_DEFAULTS = {
    "payment_card": settings.payment_card,
    "card_owner": settings.card_owner,
    "payment_bank": "",
    "payment_reference": "",
    "support_username": settings.support_username,
}


async def get_payment_settings() -> dict[str, str]:
    async with async_session() as session:
        rows = (
            await session.execute(
                select(AdminSetting).where(AdminSetting.key.in_(PAYMENT_SETTING_DEFAULTS))
            )
        ).scalars()
        saved_values = {row.key: row.value for row in rows}

    return {
        key: saved_values.get(key, default)
        for key, default in PAYMENT_SETTING_DEFAULTS.items()
    }


async def save_payment_setting(key: str, value: str) -> bool:
    if key not in PAYMENT_SETTING_DEFAULTS:
        return False

    async with async_session() as session:
        setting = await session.scalar(select(AdminSetting).where(AdminSetting.key == key))
        if setting is None:
            setting = AdminSetting(key=key, value=value)
            session.add(setting)
        else:
            setting.value = value
        await session.commit()
    return True


async def get_dashboard_stats() -> dict[str, int]:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    completed_status = OrderStatus.COMPLETED.value

    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id))) or 0
        today_orders = await session.scalar(
            select(func.count(Order.id)).where(
                Order.created_at >= today_start,
                Order.created_at < tomorrow_start,
            )
        ) or 0
        today_sales = await session.scalar(
            select(func.coalesce(func.sum(Order.price), 0)).where(
                Order.status == completed_status,
                Order.created_at >= today_start,
                Order.created_at < tomorrow_start,
            )
        ) or 0
        total_sales = await session.scalar(
            select(func.coalesce(func.sum(Order.price), 0)).where(Order.status == completed_status)
        ) or 0
        pending_payments = await session.scalar(
            select(func.count(Order.id)).where(
                Order.status.in_((OrderStatus.PENDING_PAYMENT.value, OrderStatus.WAITING_REVIEW.value))
            )
        ) or 0

    return {
        "total_users": total_users,
        "today_orders": today_orders,
        "today_sales": today_sales,
        "total_sales": total_sales,
        "pending_payments": pending_payments,
    }


async def find_users(query: str) -> list[User]:
    normalized_query = query.strip()
    async with async_session() as session:
        if normalized_query.isdigit():
            statement = select(User).where(User.telegram_id == int(normalized_query))
        else:
            username = normalized_query.removeprefix("@")
            statement = select(User).where(User.username.ilike(f"%{username}%"))
        return list((await session.execute(statement.order_by(User.id.desc()).limit(20))).scalars())


async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)


async def set_user_blocked(user_id: int, is_blocked: bool) -> User | None:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            return None
        user.is_blocked = is_blocked
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_orders(user_id: int) -> list[Order]:
    async with async_session() as session:
        orders = (
            await session.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        for order in orders:
            await session.refresh(order, attribute_names=["plan"])
        return list(orders)


async def get_recent_orders() -> list[Order]:
    async with async_session() as session:
        orders = (
            await session.execute(select(Order).order_by(Order.created_at.desc()).limit(20))
        ).scalars().all()
        for order in orders:
            await session.refresh(order, attribute_names=["user", "plan"])
        return list(orders)


async def get_order(order_id: int) -> Order | None:
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            return None
        await session.refresh(order, attribute_names=["user", "plan"])
        return order


async def get_broadcast_recipient_ids() -> list[int]:
    async with async_session() as session:
        return list(
            (
                await session.execute(
                    select(User.telegram_id).where(User.is_blocked.is_(False))
                )
            ).scalars()
        )
