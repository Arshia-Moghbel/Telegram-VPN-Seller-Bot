

from aiogram.utils.keyboard import InlineKeyboardBuilder


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