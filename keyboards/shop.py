from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_plans_keyboard(plans):
    keyboard = []

    for plan in plans:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{plan.name} - {plan.price:,} تومان",
                    callback_data=f"plan_{plan.id}"
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )