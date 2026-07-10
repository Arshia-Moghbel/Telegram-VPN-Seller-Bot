from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


plans_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🥉 یک ماهه - 100,000 تومان",
                callback_data="plan_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="🥈 سه ماهه - 270,000 تومان",
                callback_data="plan_3"
            )
        ],
        [
            InlineKeyboardButton(
                text="🥇 شش ماهه - 500,000 تومان",
                callback_data="plan_6"
            )
        ]
    ]
)