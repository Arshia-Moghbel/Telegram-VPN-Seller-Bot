from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def tariffs_keyboard(plans) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"خرید {plan.name} — {plan.price:,} تومان",
            callback_data=f"plan_{plan.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def connection_guides_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 اندروید", callback_data="guide_android")],
            [InlineKeyboardButton(text="🍎 آیفون / آیپد", callback_data="guide_ios")],
            [InlineKeyboardButton(text="🪟 ویندوز", callback_data="guide_windows")],
            [InlineKeyboardButton(text="💻 مک", callback_data="guide_macos")],
        ]
    )


def support_keyboard(username: str) -> InlineKeyboardMarkup | None:
    normalized_username = username.strip().removeprefix("@")
    if not normalized_username:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 ارتباط با پشتیبانی",
                    url=f"https://t.me/{normalized_username}",
                )
            ]
        ]
    )
