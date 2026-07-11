

from aiogram import Router, F
from aiogram import Bot
from aiogram.types import Message, CallbackQuery

from config import settings
from db import async_session
from database.models import Order
from models.order_status import OrderStatus
from sqlalchemy import select

router = Router()


@router.message()
async def admin_entry(message: Message):
    if message.from_user.id != settings.admin_id:
        return

    await message.answer(
        "🛠 پنل ادمین آماده است.\n\n"
        "در مرحله بعد قابلیت بررسی رسیدها و دکمه‌های تأیید/رد به این بخش اضافه می‌شود."
    )


@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Access denied", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return
        await session.refresh(order, attribute_names=["user"])
        order.status = OrderStatus.PAID.value
        await session.commit()

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ پرداخت تایید شد."
    )

    await bot.send_message(
        chat_id=order.user.telegram_id,
        text=(
            "✅ پرداخت شما تایید شد.\n\n"
            "سفارش شما در حال آماده سازی است و به زودی کانفیگ VPN برایتان ارسال خواهد شد."
        )
    )

    await callback.answer("سفارش تایید شد.")


@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Access denied", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return

        await session.refresh(order, attribute_names=["user"])
        order.status = OrderStatus.CANCELED.value
        await session.commit()

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ پرداخت رد شد."
    )

    await bot.send_message(
        chat_id=order.user.telegram_id,
        text="❌ پرداخت شما تایید نشد. لطفاً با پشتیبانی تماس بگیرید یا رسید صحیح را دوباره ارسال کنید."
    )

    await callback.answer("سفارش رد شد.")