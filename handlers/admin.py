from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from keyboards.admin import admin_panel_keyboard

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != settings.admin_id:
        await message.answer(
            "⛔ شما دسترسی به این بخش را ندارید."
        )
        return

    await message.answer(
        "🛠 پنل مدیریت",
        reply_markup=admin_panel_keyboard(),
    )