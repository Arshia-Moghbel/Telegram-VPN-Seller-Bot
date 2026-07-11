

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from aiogram import Bot
from sqlalchemy import select

from config import settings
from db import async_session
from database.models import Order, User, Plan
from keyboards.admin import receipt_review_keyboard

from states.payment import PaymentState
from services.payment_service import save_receipt


router = Router()


@router.message(PaymentState.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    order_id = data.get("order_id")

    if order_id is None:
        await message.answer(
            "❌ سفارش پیدا نشد. لطفاً دوباره تلاش کنید."
        )
        await state.clear()
        return

    file_id = message.photo[-1].file_id

    receipt = await save_receipt(
        order_id=order_id,
        telegram_file_id=file_id
    )

    if receipt is None:
        await message.answer(
            "❌ ذخیره رسید انجام نشد. لطفاً دوباره تلاش کنید."
        )
        return

    await state.clear()

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one()

        await session.refresh(order, attribute_names=["user", "plan"])

    await bot.send_photo(
        chat_id=settings.admin_id,
        photo=file_id,
        caption=(
            f"🛒 سفارش جدید\n\n"
            f"🆔 سفارش: #{order.id}\n"
            f"👤 کاربر: {order.user.telegram_id}\n"
            f"📦 پلن: {order.plan.name}\n"
            f"💰 مبلغ: {order.plan.price:,} تومان"
        ),
        reply_markup=await receipt_review_keyboard(order.id)
    )

    await message.answer(
        "✅ رسید شما دریافت شد.\n\n"
        "در حال بررسی توسط پشتیبانی است."
    )


@router.message(PaymentState.waiting_for_receipt)
async def invalid_receipt(message: Message):
    await message.answer(
        "❌ لطفاً فقط تصویر رسید پرداخت را ارسال کنید."
    )