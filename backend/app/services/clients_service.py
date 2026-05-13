"""Client service — SQLAlchemy async ORM CRUD."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Client
from app.schemas.parser import ClientCreateSchema, ClientUpdateSchema


async def find_client(db: AsyncSession, client_id: str) -> Optional[Client]:
    try:
        uid = uuid.UUID(client_id)
    except ValueError:
        return None
    result = await db.execute(select(Client).where(Client.id == uid))
    return result.scalar_one_or_none()


async def list_clients(db: AsyncSession) -> list[Client]:
    result = await db.execute(select(Client).order_by(Client.created_at.desc()))
    return list(result.scalars().all())


async def create_client(db: AsyncSession, data: ClientCreateSchema) -> Client:
    client = Client(
        id=uuid.uuid4(),
        name=data.name,
        inn=data.inn,
        contacts=data.contacts,
        created_at=datetime.now(timezone.utc),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def update_client(db: AsyncSession, client_id: str, data: ClientUpdateSchema) -> Optional[Client]:
    client = await find_client(db, client_id)
    if not client:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(client, key, value)
    await db.commit()
    await db.refresh(client)
    return client


async def delete_client(db: AsyncSession, client_id: str) -> bool:
    client = await find_client(db, client_id)
    if not client:
        return False
    await db.delete(client)
    await db.commit()
    return True


async def get_client_projects(db: AsyncSession, client_id: str) -> list[dict]:
    c = await find_client(db, client_id)
    if not c:
        return []
    # Projects are loaded via ORM relationship (eager by default)
    return [
        {
            "id": str(p.id),
            "external_code": p.external_code,
            "name": p.name,
            "stage": p.stage,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in (c.projects or [])
    ]
