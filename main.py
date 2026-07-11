from services.seed import create_default_plans
from handlers.shop import router as shop_router
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db import create_db

from handlers.start import router


async def main():
    logging.basicConfig(level=logging.INFO)

    await create_db()
    await create_default_plans()

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    dp.include_router(shop_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())