"""Provider-independent preparation for automatic VPN provisioning.

No host, panel address, password, or API token is required (or used) here.
When a panel is chosen later, its adapter can use the selected server and the
credential environment-variable name without changing order handling.
"""

from dataclasses import dataclass

from sqlalchemy import func, select

from database.models import ProvisioningAttempt, VPNServer
from db import async_session


@dataclass(frozen=True)
class ProvisioningSelection:
    server_id: int
    server_name: str


async def select_server_for_provisioning(order_id: int) -> ProvisioningSelection | None:
    """Choose the least-used active server, then honour priority and name."""
    async with async_session() as session:
        existing = await session.scalar(
            select(ProvisioningAttempt).where(ProvisioningAttempt.order_id == order_id)
        )
        if existing is not None:
            server = await session.get(VPNServer, existing.server_id)
            return ProvisioningSelection(server.id, server.name) if server else None

        load = (
            select(ProvisioningAttempt.server_id, func.count(ProvisioningAttempt.id).label("accounts"))
            .where(ProvisioningAttempt.status.in_(("pending", "provisioned")))
            .group_by(ProvisioningAttempt.server_id)
            .subquery()
        )
        rows = await session.execute(
            select(VPNServer, func.coalesce(load.c.accounts, 0).label("accounts"))
            .outerjoin(load, VPNServer.id == load.c.server_id)
            .where(VPNServer.is_active.is_(True))
            .order_by(func.coalesce(load.c.accounts, 0), VPNServer.priority, VPNServer.name)
        )
        for server, accounts in rows:
            if server.max_accounts is not None and accounts >= server.max_accounts:
                continue
            session.add(ProvisioningAttempt(order_id=order_id, server_id=server.id))
            await session.commit()
            return ProvisioningSelection(server.id, server.name)
    return None


async def get_servers() -> list[VPNServer]:
    async with async_session() as session:
        return list((await session.execute(select(VPNServer).order_by(VPNServer.priority, VPNServer.name))).scalars())


async def add_server(
    name: str, location: str, protocol: str, priority: int = 100, max_accounts: int | None = None
) -> VPNServer:
    async with async_session() as session:
        server = VPNServer(
            name=name.strip(), location=location.strip(), protocol=protocol.strip(),
            priority=priority, max_accounts=max_accounts,
        )
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return server
