from sqlalchemy import select

from db import async_session
from database.models import Plan


async def create_default_plans():
    async with async_session() as session:

        result = await session.execute(
            select(Plan)
        )

        plans = result.scalars().all()

        if plans:
            return

        default_plans = [
            Plan(
                name="اقتصادی",
                price=100000,
                duration=1,
                traffic="100GB",
            ),
            Plan(
                name="استاندارد",
                price=270000,
                duration=3,
                traffic="300GB",
            ),
            Plan(
                name="حرفه‌ای",
                price=500000,
                duration=6,
                traffic="700GB",
            ),
        ]

        session.add_all(default_plans)
        await session.commit()