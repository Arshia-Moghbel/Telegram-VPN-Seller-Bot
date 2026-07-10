from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.shop import plans_keyboard

router = Router()


@router.message(F.text == "🛒 خرید VPN")
async def buy_vpn(message: Message):
    await message.answer(
        "🛒 پلن موردنظر خود را انتخاب کنید:",
        reply_markup=plans_keyboard
    )


@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):

    plan = callback.data.split("_")[1]

    plans = {
        "1": ("یک ماهه", 100000),
        "3": ("سه ماهه", 270000),
        "6": ("شش ماهه", 500000),
    }

    name, price = plans[plan]

    await callback.message.answer(
        f"✅ پلن انتخاب شد:\n\n"
        f"📦 اشتراک: {name}\n"
        f"💰 مبلغ: {price:,} تومان\n\n"
        f"لطفاً پرداخت را انجام دهید و رسید را ارسال کنید."
    )

    await callback.answer()