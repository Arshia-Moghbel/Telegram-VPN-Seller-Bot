from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 مدیریت پلن‌ها",
                    callback_data="admin_plans",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 تنظیمات پرداخت",
                    callback_data="admin_payment",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📑 سفارش‌ها",
                    callback_data="admin_orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 کاربران",
                    callback_data="admin_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 آمار",
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 ارسال همگانی",
                    callback_data="admin_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="admin_settings",
                )
            ],
        ]
    )


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ بازگشت به پنل", callback_data="admin_home")]
        ]
    )


def payment_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 شماره کارت", callback_data="admin_setting_payment_card")],
            [InlineKeyboardButton(text="👤 نام صاحب حساب", callback_data="admin_setting_card_owner")],
            [InlineKeyboardButton(text="🏦 بانک", callback_data="admin_setting_payment_bank")],
            [InlineKeyboardButton(text="🔖 شناسه پرداخت", callback_data="admin_setting_payment_reference")],
            [InlineKeyboardButton(text="💬 پشتیبانی", callback_data="admin_setting_support_username")],
            [InlineKeyboardButton(text="◀️ بازگشت به پنل", callback_data="admin_home")],
        ]
    )


def users_keyboard(users) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        username = f"@{user.username}" if user.username else "بدون نام کاربری"
        status = "🚫" if user.is_blocked else "✅"
        builder.button(
            text=f"{status} {user.telegram_id} — {username}",
            callback_data=f"admin_user_{user.id}",
        )
    builder.button(text="🔎 جستجوی کاربر", callback_data="admin_users_search")
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
    builder.adjust(1)
    return builder.as_markup()


def user_details_keyboard(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
    action_text = "✅ آزاد کردن" if is_blocked else "🚫 مسدود کردن"
    action = "unblock" if is_blocked else "block"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=action_text, callback_data=f"admin_user_{action}_{user_id}")],
            [InlineKeyboardButton(text="🧾 سوابق خرید", callback_data=f"admin_user_orders_{user_id}")],
            [InlineKeyboardButton(text="◀️ بازگشت به پنل", callback_data="admin_home")],
        ]
    )


def orders_keyboard(orders) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=f"#{order.id} — {order.plan.name} — {order.price:,} تومان",
            callback_data=f"admin_order_{order.id}",
        )
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
    builder.adjust(1)
    return builder.as_markup()


def plans_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ افزودن پلن", callback_data="plan_add")
    builder.button(text="📋 فهرست پلن‌ها", callback_data="plan_list")
    builder.adjust(1)
    return builder.as_markup()


def plan_list_keyboard(plans):
    builder = InlineKeyboardBuilder()
    for plan in plans:
        status = "✅" if plan.is_active else "⛔️"
        builder.button(
            text=f"{status} {plan.name} — {plan.price:,} تومان",
            callback_data=f"plan_open_{plan.id}",
        )
    builder.button(text="➕ افزودن پلن", callback_data="plan_add")
    builder.adjust(1)
    return builder.as_markup()


def plan_details_keyboard(plan_id: int, is_active: bool):
    builder = InlineKeyboardBuilder()
    for field, label in (
        ("name", "✏️ نام"),
        ("price", "💰 قیمت"),
        ("duration", "📅 مدت"),
        ("traffic", "📶 حجم"),
        ("description", "📝 توضیحات"),
    ):
        builder.button(text=label, callback_data=f"plan_edit_{plan_id}_{field}")
    toggle_label = "⛔️ غیرفعال‌کردن" if is_active else "✅ فعال‌کردن"
    builder.button(text=toggle_label, callback_data=f"plan_toggle_{plan_id}")
    builder.button(text="🗑 حذف", callback_data=f"plan_delete_{plan_id}")
    builder.button(text="◀️ بازگشت", callback_data="plan_list")
    builder.adjust(2, 2, 1, 1, 1)
    return builder.as_markup()


def confirm_plan_deletion_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 بله، حذف شود", callback_data=f"plan_delete_confirm_{plan_id}")],
            [InlineKeyboardButton(text="◀️ انصراف", callback_data=f"plan_open_{plan_id}")],
        ]
    )


async def receipt_review_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ تایید", callback_data=f"approve_order_{order_id}")
    builder.button(text="❌ رد", callback_data=f"reject_order_{order_id}")
    builder.adjust(2)
    return builder.as_markup()
