from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_keyboard(labels: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_plans"],
                    callback_data="admin_plans",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_payment"],
                    callback_data="admin_payment",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_content"],
                    callback_data="admin_content",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_orders"],
                    callback_data="admin_orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_users"],
                    callback_data="admin_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_stats"],
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_broadcast"],
                    callback_data="admin_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_coupons"],
                    callback_data="admin_coupons",
                )
            ],
            [
                InlineKeyboardButton(
                    text=labels["ui_admin_buttons"],
                    callback_data="admin_buttons",
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


def cancel_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ لغو و بازگشت", callback_data="admin_cancel_flow")]
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


def content_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👋 پیام خوش‌آمد", callback_data="admin_setting_content_welcome")],
            [InlineKeyboardButton(text="⛔ پیام مسدودی", callback_data="admin_setting_content_blocked")],
            [InlineKeyboardButton(text="🌍 متن سرورها", callback_data="admin_setting_content_servers")],
            [InlineKeyboardButton(text="📖 منوی آموزش", callback_data="admin_setting_content_guides_menu")],
            [InlineKeyboardButton(text="🤖 آموزش اندروید", callback_data="admin_setting_content_guide_android")],
            [InlineKeyboardButton(text="🍎 آموزش iPhone/iPad", callback_data="admin_setting_content_guide_ios")],
            [InlineKeyboardButton(text="🪟 آموزش ویندوز", callback_data="admin_setting_content_guide_windows")],
            [InlineKeyboardButton(text="💻 آموزش مک", callback_data="admin_setting_content_guide_macos")],
            [InlineKeyboardButton(text="📞 متن پشتیبانی", callback_data="admin_setting_content_support")],
            [InlineKeyboardButton(text="🛒 متن خرید و پلن‌ها", callback_data="admin_setting_content_choose_plan")],
            [InlineKeyboardButton(text="🎟 متن‌های تخفیف", callback_data="admin_content_coupons")],
            [InlineKeyboardButton(text="💳 متن‌های پرداخت", callback_data="admin_content_payment")],
            [InlineKeyboardButton(text="◀️ بازگشت به پنل", callback_data="admin_home")],
        ]
    )


def content_group_keyboard(keys: tuple[str, ...]) -> InlineKeyboardMarkup:
    labels = {
        "content_support_unavailable": "پشتیبانی تنظیم نشده",
        "content_no_plans": "پلنی موجود نیست",
        "content_coupon_prompt": "درخواست کد تخفیف",
        "content_coupon_cancelled": "لغو کد تخفیف",
        "content_coupon_invalid": "کد تخفیف نامعتبر",
        "content_coupon_applied": "کد تخفیف اعمال شد",
        "content_coupon_active": "نمایش کد فعال",
        "content_coupon_expired": "کد منقضی شده",
        "content_payment_unavailable": "پرداخت غیرفعال",
        "content_payment_details_missing": "اطلاعات کارت موجود نیست",
        "content_order_created": "سفارش ثبت شد",
        "content_order_failed": "خطای ثبت سفارش",
        "content_receipt_cancelled": "لغو ارسال رسید",
        "content_receipt_unavailable": "رسید قابل دریافت نیست",
        "content_receipt_forward_failed": "خطای ارسال رسید",
        "content_receipt_received": "رسید دریافت شد",
        "content_order_not_found": "سفارش پیدا نشد",
        "content_receipt_image_only": "درخواست تصویر رسید",
    }
    builder = InlineKeyboardBuilder()
    for key in keys:
        builder.button(text=labels[key], callback_data=f"admin_setting_{key}")
    builder.button(text="◀️ بازگشت به متن‌ها", callback_data="admin_content")
    builder.adjust(1)
    return builder.as_markup()


def button_settings_keyboard(labels: dict[str, str]) -> InlineKeyboardMarkup:
    keys = (
        "ui_public_buy", "ui_public_servers", "ui_public_guides", "ui_public_support",
        "ui_coupon_enter", "ui_guide_android", "ui_guide_ios", "ui_guide_windows",
        "ui_guide_macos", "ui_support_contact",
        "ui_admin_plans", "ui_admin_payment", "ui_admin_content", "ui_admin_orders",
        "ui_admin_users", "ui_admin_stats", "ui_admin_broadcast", "ui_admin_coupons",
        "ui_admin_buttons",
    )
    builder = InlineKeyboardBuilder()
    for key in keys:
        builder.button(text=labels[key], callback_data=f"admin_setting_{key}")
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
    builder.adjust(1)
    return builder.as_markup()


def coupons_keyboard(coupons) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ افزودن کد تخفیف", callback_data="coupon_add")
    for coupon in coupons:
        status = "✅" if coupon.is_active else "⛔️"
        kind = "٪" if coupon.discount_type == "percent" else "تومان"
        limit = str(coupon.max_uses) if coupon.max_uses is not None else "∞"
        builder.button(
            text=f"{status} {coupon.code} — {coupon.value}{kind} ({coupon.uses_count}/{limit})",
            callback_data=f"coupon_toggle_{coupon.id}",
        )
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
    builder.adjust(1)
    return builder.as_markup()


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
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
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
    builder.button(text="◀️ بازگشت به پنل", callback_data="admin_home")
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
