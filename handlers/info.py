from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from filters.button_text import ButtonTextFilter

from keyboards.info import connection_guides_keyboard, support_keyboard
from services.admin_service import get_content_settings, get_payment_settings, get_ui_labels
from services.content_service import GUIDE_CONTENT_KEYS

router = Router()


@router.message(ButtonTextFilter("ui_public_servers"))
async def show_servers(message: Message):
    content = await get_content_settings()
    await message.answer(content["content_servers"])


@router.message(ButtonTextFilter("ui_public_guides"))
async def show_connection_guides(message: Message):
    content = await get_content_settings()
    await message.answer(
        content["content_guides_menu"],
        reply_markup=connection_guides_keyboard(await get_ui_labels()),
    )


@router.callback_query(F.data.startswith("guide_"))
async def show_connection_guide(callback: CallbackQuery):
    platform = callback.data.removeprefix("guide_")
    content_key = GUIDE_CONTENT_KEYS.get(platform)
    if content_key is None:
        await callback.answer("راهنما پیدا نشد.", show_alert=True)
        return

    content = await get_content_settings()
    guide = content[content_key]

    await callback.message.edit_text(guide, reply_markup=connection_guides_keyboard(await get_ui_labels()))
    await callback.answer()


@router.message(ButtonTextFilter("ui_public_support"))
async def show_support(message: Message):
    payment_settings = await get_payment_settings()
    support_username = payment_settings["support_username"]
    if not support_username:
        content = await get_content_settings()
        await message.answer(content["content_support_unavailable"])
        return

    content = await get_content_settings()
    await message.answer(
        content["content_support"],
        reply_markup=support_keyboard(support_username, await get_ui_labels()),
    )
