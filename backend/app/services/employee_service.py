"""Employee service."""
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Employee


async def list_employees(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Employee).order_by(Employee.full_name)
    )
    return [_emp_to_dict(e) for e in result.scalars().all()]


async def get_employee(db: AsyncSession, emp_id: str) -> Optional[dict]:
    try:
        uid = uuid.UUID(emp_id)
    except ValueError:
        return None
    result = await db.execute(select(Employee).where(Employee.id == uid))
    e = result.scalar_one_or_none()
    return _emp_to_dict(e) if e else None


async def create_employee(db: AsyncSession, data: dict) -> dict:
    e = Employee(
        id=uuid.uuid4(),
        full_name=data["full_name"],
        telegram_id=data.get("telegram_id"),
        role=data.get("role", "worker"),
        department=data.get("department"),
        is_active=data.get("is_active", True),
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return _emp_to_dict(e)


async def update_employee(db: AsyncSession, emp_id: str, data: dict) -> Optional[dict]:
    try:
        uid = uuid.UUID(emp_id)
    except ValueError:
        return None
    result = await db.execute(select(Employee).where(Employee.id == uid))
    e = result.scalar_one_or_none()
    if not e:
        return None
    for k, v in data.items():
        if v is not None and hasattr(e, k):
            setattr(e, k, v)
    await db.commit()
    await db.refresh(e)
    return _emp_to_dict(e)


async def delete_employee(db: AsyncSession, emp_id: str) -> bool:
    try:
        uid = uuid.UUID(emp_id)
    except ValueError:
        return False
    result = await db.execute(select(Employee).where(Employee.id == uid))
    e = result.scalar_one_or_none()
    if not e:
        return False
    await db.delete(e)
    await db.commit()
    return True


def _emp_to_dict(e: Employee) -> dict:
    return {
        "id": str(e.id),
        "full_name": e.full_name,
        "telegram_id": e.telegram_id,
        "role": e.role.value if e.role else "worker",
        "department": e.department,
        "is_active": e.is_active,
    }
