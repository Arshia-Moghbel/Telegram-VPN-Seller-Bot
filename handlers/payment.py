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
from services.admin_service import get_content_settings


router = Router()
logger = logging.getLogger(__name__)


@router.message(PaymentState.waiting_for_receipt, F.text.casefold() == "cancel")
async def cancel_receipt(message: Message, state: FSMContext):
    await state.clear()
    content = await get_content_settings()
    await message.answer(content["content_receipt_cancelled"])


async def process_receipt(message: Message, bot: Bot, order_id: int) -> bool:
    content = await get_content_settings()
    file_id = message.photo[-1].file_id

    receipt = await save_receipt(
        order_id=order_id,
        telegram_file_id=file_id,
        telegram_id=message.from_user.id,
    )

    if receipt is None:
        await message.answer(content["content_receipt_unavailable"])
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
        await message.answer(content["content_receipt_forward_failed"])
        return False

    await message.answer(content["content_receipt_received"])
    return True


@router.message(PaymentState.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    order_id = (await state.get_data()).get("order_id")
    if order_id is None:
        await state.clear()
        content = await get_content_settings()
        await message.answer(content["content_order_not_found"])
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
    content = await get_content_settings()
    await message.answer(content["content_receipt_image_only"])
