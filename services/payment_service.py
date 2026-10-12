from database.models import Receipt, Order, User
from db import async_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from models.order_status import OrderStatus


async def save_receipt(
    order_id: int,
    telegram_file_id: str,
    telegram_id: int,
) -> Receipt | None:
    async with async_session() as session:

        result = await session.execute(
            select(Order).join(User).where(
                Order.id == order_id,
                User.telegram_id == telegram_id,
                User.is_blocked.is_(False),
                Order.status == OrderStatus.PENDING_PAYMENT.value,
            )
        )

        order = result.scalar_one_or_none()

        if order is None:
            return None

        receipt = Receipt(
            order_id=order.id,
            telegram_file_id=telegram_file_id
        )

        order.status = OrderStatus.WAITING_REVIEW.value

        session.add(receipt)

        try:
            await session.commit()
        except IntegrityError:
            # A duplicate update can race with the first receipt submission.
            # Keep the original receipt and report this attempt as unavailable.
            await session.rollback()
            return None

        await session.refresh(receipt)

        return receipt


async def discard_receipt(order_id: int) -> None:
    """Make a receipt retryable when Telegram could not notify the admin."""
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None or order.status != OrderStatus.WAITING_REVIEW.value:
            return
        receipt = await session.scalar(select(Receipt).where(Receipt.order_id == order_id))
        if receipt is not None:
            await session.delete(receipt)
        order.status = OrderStatus.PENDING_PAYMENT.value
        await session.commit()
