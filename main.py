from services.seed import create_default_plans
from handlers.shop import router as shop_router
from handlers.payment import router as payment_router
from handlers.start import router
from handlers.admin import router as admin_router
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import settings
from db import create_db



async def main():
    logging.basicConfig(level=logging.INFO)

    await create_db()
    await create_default_plans()

    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(router)
    dp.include_router(shop_router)
    dp.include_router(payment_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
