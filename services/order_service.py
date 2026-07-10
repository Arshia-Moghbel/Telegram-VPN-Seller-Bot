from db import async_session
from database.models import Order, User, Plan
from sqlalchemy import select


async def create_order(
    telegram_id: int,
    plan_id: int
):
    async with async_session() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            return None


        plan_result = await session.execute(
            select(Plan).where(
                Plan.id == plan_id
            )
        )

        plan = plan_result.scalar_one_or_none()

        if plan is None:
            return None


        order = Order(
            user_id=user.id,
            plan_id=plan.id,
            price=plan.price,
            status="pending_payment"
        )

        session.add(order)

        await session.commit()

        await session.refresh(order)

        return order