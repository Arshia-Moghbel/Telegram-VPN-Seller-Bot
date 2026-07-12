from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.info import connection_guides_keyboard, support_keyboard, tariffs_keyboard
from services.admin_service import get_payment_settings
from services.content_service import (
    CONNECTION_GUIDES,
    format_servers,
    format_tariffs,
    get_active_plans,
)

router = Router()


@router.message(F.text == "💎 تعرفه‌ها")
async def show_tariffs(message: Message):
    plans = await get_active_plans()
    if not plans:
        await message.answer("در حال حاضر هیچ تعرفه فعالی وجود ندارد.")
        return

    await message.answer(format_tariffs(plans), reply_markup=tariffs_keyboard(plans))


@router.message(F.text == "🌍 سرورها")
async def show_servers(message: Message):
    await message.answer(format_servers())


@router.message(F.text == "📖 آموزش اتصال")
async def show_connection_guides(message: Message):
    await message.answer(
        "📖 آموزش اتصال\n\nدستگاه خود را انتخاب کنید:",
        reply_markup=connection_guides_keyboard(),
    )


@router.callback_query(F.data.startswith("guide_"))
async def show_connection_guide(callback: CallbackQuery):
    platform = callback.data.removeprefix("guide_")
    guide = CONNECTION_GUIDES.get(platform)
    if guide is None:
        await callback.answer("راهنما پیدا نشد.", show_alert=True)
        return

    await callback.message.edit_text(guide, reply_markup=connection_guides_keyboard())
    await callback.answer()


@router.message(F.text == "📞 پشتیبانی")
async def show_support(message: Message):
    payment_settings = await get_payment_settings()
    support_username = payment_settings["support_username"]
    if not support_username:
        await message.answer("اطلاعات پشتیبانی هنوز تنظیم نشده است. لطفاً بعداً دوباره تلاش کنید.")
        return

    await message.answer(
        "📞 پشتیبانی\n\n"
        "برای پیگیری سفارش، مشکل اتصال یا پرسش‌های پیش از خرید، پیام بدهید.",
        reply_markup=support_keyboard(support_username),
    )
