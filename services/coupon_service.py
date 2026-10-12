from database.models import Coupon, CouponRedemption, User
from db import async_session
from sqlalchemy import select


def normalize_coupon_code(code: str) -> str:
    return code.strip().upper()


def discount_for_price(coupon: Coupon, price: int) -> int:
    if coupon.discount_type == "percent":
        return min(price, price * coupon.value // 100)
    return min(price, coupon.value)


async def get_coupon(code: str) -> Coupon | None:
    normalized = normalize_coupon_code(code)
    async with async_session() as session:
        coupon = await session.scalar(select(Coupon).where(Coupon.code == normalized))
        if coupon is None or not coupon.is_active:
            return None
        if coupon.max_uses is not None and coupon.uses_count >= coupon.max_uses:
            return None
        return coupon


async def create_coupon(code: str, discount_type: str, value: int, max_uses: int | None) -> Coupon:
    coupon = Coupon(
        code=normalize_coupon_code(code),
        discount_type=discount_type,
        value=value,
        max_uses=max_uses,
    )
    async with async_session() as session:
        session.add(coupon)
        await session.commit()
        await session.refresh(coupon)
    return coupon


async def get_coupons(limit: int = 30) -> list[Coupon]:
    async with async_session() as session:
        return list((await session.execute(select(Coupon).order_by(Coupon.id.desc()).limit(limit))).scalars())


async def toggle_coupon(coupon_id: int) -> Coupon | None:
    async with async_session() as session:
        coupon = await session.get(Coupon, coupon_id)
        if coupon is None:
            return None
        coupon.is_active = not coupon.is_active
        await session.commit()
        await session.refresh(coupon)
        return coupon
