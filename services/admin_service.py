from datetime import datetime, timedelta

from sqlalchemy import func, select

from config import settings
from database.models import AdminSetting, Order, User
from db import async_session
from models.order_status import OrderStatus
from services.content_service import CONTENT_DEFAULTS


PAYMENT_SETTING_DEFAULTS = {
    "payment_card": settings.payment_card,
    "card_owner": settings.card_owner,
    "payment_bank": "",
    "payment_reference": "",
    "support_username": settings.support_username,
}
EDITABLE_SETTING_DEFAULTS = PAYMENT_SETTING_DEFAULTS | CONTENT_DEFAULTS

UI_LABEL_DEFAULTS = {
    "ui_public_buy": "🛒 خرید VPN",
    "ui_public_servers": "🌍 سرورها",
    "ui_public_guides": "📖 آموزش اتصال",
    "ui_public_support": "📞 پشتیبانی",
    "ui_coupon_enter": "🎟 وارد کردن کد تخفیف",
    "ui_guide_android": "🤖 اندروید",
    "ui_guide_ios": "🍎 آیفون / آیپد",
    "ui_guide_windows": "🪟 ویندوز",
    "ui_guide_macos": "💻 مک",
    "ui_support_contact": "💬 ارتباط با پشتیبانی",
    "ui_admin_plans": "📦 مدیریت پلن‌ها",
    "ui_admin_payment": "💳 تنظیمات پرداخت",
    "ui_admin_content": "📝 متن‌های ربات",
    "ui_admin_orders": "📑 سفارش‌ها",
    "ui_admin_users": "👥 کاربران",
    "ui_admin_stats": "📊 آمار",
    "ui_admin_broadcast": "📢 ارسال همگانی",
    "ui_admin_buttons": "🔘 تنظیم دکمه‌ها",
    "ui_admin_coupons": "🎟 کدهای تخفیف",
}
EDITABLE_SETTING_DEFAULTS |= UI_LABEL_DEFAULTS

# There is currently one configured administrator.  Persisting this value means
# a restart does not strand an approved order before its VPN configuration is
# delivered.
ACTIVE_FULFILLMENT_ORDER_KEY = "active_fulfillment_order_id"


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
    if key not in EDITABLE_SETTING_DEFAULTS:
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


async def get_content_settings() -> dict[str, str]:
    async with async_session() as session:
        rows = (
            await session.execute(
                select(AdminSetting).where(AdminSetting.key.in_(CONTENT_DEFAULTS))
            )
        ).scalars()
        saved_values = {row.key: row.value for row in rows}
    return {key: saved_values.get(key, default) for key, default in CONTENT_DEFAULTS.items()}


async def get_ui_labels() -> dict[str, str]:
    async with async_session() as session:
        rows = (
            await session.execute(
                select(AdminSetting).where(AdminSetting.key.in_(UI_LABEL_DEFAULTS))
            )
        ).scalars()
        saved_values = {row.key: row.value for row in rows}
    return {key: saved_values.get(key, default) for key, default in UI_LABEL_DEFAULTS.items()}


async def get_active_fulfillment_order_id() -> int | None:
    async with async_session() as session:
        value = await session.scalar(
            select(AdminSetting.value).where(AdminSetting.key == ACTIVE_FULFILLMENT_ORDER_KEY)
        )
    try:
        order_id = int(value) if value else None
    except (TypeError, ValueError):
        return None
    return order_id if order_id and order_id > 0 else None


async def set_active_fulfillment_order_id(order_id: int | None) -> None:
    async with async_session() as session:
        setting = await session.scalar(
            select(AdminSetting).where(AdminSetting.key == ACTIVE_FULFILLMENT_ORDER_KEY)
        )
        value = str(order_id) if order_id is not None else ""
        if setting is None:
            session.add(AdminSetting(key=ACTIVE_FULFILLMENT_ORDER_KEY, value=value))
        else:
            setting.value = value
        await session.commit()


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


async def get_users(limit: int = 50) -> list[User]:
    async with async_session() as session:
        return list(
            (
                await session.execute(select(User).order_by(User.created_at.desc()).limit(limit))
            ).scalars()
        )


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
