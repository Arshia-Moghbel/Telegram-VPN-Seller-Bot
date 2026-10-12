"""Read-only readiness probe for Docker and server monitoring."""

import asyncio

from aiogram import Bot

from config import settings, validate_settings


async def main() -> None:
    validate_settings()
    bot = Bot(settings.bot_token)
    try:
        await bot.get_me(request_timeout=10)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
