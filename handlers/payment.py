import logging

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
from services.payment_service import discard_receipt, save_receipt


router = Router()
logger = logging.getLogger(__name__)


@router.message(PaymentState.waiting_for_receipt, F.text.casefold() == "cancel")
async def cancel_receipt(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ ارسال رسید لغو شد. می‌توانید دوباره از بخش خرید اقدام کنید.")


async def process_receipt(message: Message, bot: Bot, order_id: int) -> bool:
    file_id = message.photo[-1].file_id

    receipt = await save_receipt(
        order_id=order_id,
        telegram_file_id=file_id,
        telegram_id=message.from_user.id,
    )

    if receipt is None:
        await message.answer(
            "❌ این سفارش دیگر آمادهٔ دریافت رسید نیست. لطفاً وضعیت سفارش را بررسی کنید."
        )
        return False

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one()

        await session.refresh(order, attribute_names=["user", "plan"])

    try:
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
            reply_markup=await receipt_review_keyboard(order.id),
        )
    except TelegramAPIError:
        logger.exception("Could not forward receipt for order %s to the administrator", order_id)
        await discard_receipt(order_id)
        await message.answer(
            "❌ ارسال رسید برای پشتیبانی ناموفق بود. لطفاً چند لحظه دیگر دوباره تلاش کنید."
        )
        return False

    await message.answer(
        "✅ رسید شما دریافت شد.\n\n"
        "در حال بررسی توسط پشتیبانی است."
    )
    return True


@router.message(PaymentState.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    order_id = (await state.get_data()).get("order_id")
    if order_id is None:
        await state.clear()
        await message.answer("❌ سفارش پیدا نشد. لطفاً دوباره از بخش خرید اقدام کنید.")
        return
    if await process_receipt(message, bot, order_id):
        await state.clear()


@router.message(F.photo)
async def receive_receipt_after_restart(message: Message, bot: Bot):
    """Recover the active payment flow when in-memory FSM storage was reset."""
    async with async_session() as session:
        orders = list(
            (
                await session.execute(
                    select(Order.id)
                    .join(User)
                    .where(
                        User.telegram_id == message.from_user.id,
                        Order.status == "pending_payment",
                    )
                    .order_by(Order.created_at.desc())
                    .limit(2)
                )
            ).scalars()
        )
    if len(orders) == 1:
        await process_receipt(message, bot, orders[0])


@router.message(PaymentState.waiting_for_receipt)
async def invalid_receipt(message: Message):
    await message.answer(
        "❌ لطفاً فقط تصویر رسید پرداخت را ارسال کنید."
    )
