

from aiogram.utils.keyboard import InlineKeyboardBuilder


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
            callback_data=f"plan_open_{plan.id}"
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


async def receipt_review_keyboard(order_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ تایید",
        callback_data=f"approve_order_{order_id}"
    )

    builder.button(
        text="❌ رد",
        callback_data=f"reject_order_{order_id}"
    )

    builder.adjust(2)

    return builder.as_markup()
