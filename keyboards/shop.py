from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_plans_keyboard(plans, labels: dict[str, str]):
    keyboard = []

    for plan in plans:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{plan.name} | {plan.price:,} تومان",
                    callback_data=f"plan_{plan.id}"
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text=labels["ui_coupon_enter"], callback_data="coupon_enter")]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
