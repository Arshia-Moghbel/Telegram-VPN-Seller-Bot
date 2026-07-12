from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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