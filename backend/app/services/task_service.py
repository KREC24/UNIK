"""Task assignment service + Telegram bot integration."""
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    TaskAssignment, TaskStatus, Employee, Project, LineItem,
)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_API = "https://api.telegram.org"


async def list_tasks(db: AsyncSession, status: str = "", limit: int = 100) -> list[dict]:
    q = (
        select(TaskAssignment)
        .options(
            selectinload(TaskAssignment.employee),
            selectinload(TaskAssignment.project),
            selectinload(TaskAssignment.creator),
        )
        .order_by(TaskAssignment.created_at.desc())
    )
    if status:
        q = q.where(TaskAssignment.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return [_task_to_dict(t) for t in result.scalars().all()]


async def get_task_stats(db: AsyncSession) -> dict:
    active = await db.execute(
        select(func.count(TaskAssignment.id)).where(
            TaskAssignment.status.in_(["accepted", "in_work"])
        )
    )
    pending = await db.execute(
        select(func.count(TaskAssignment.id)).where(
            TaskAssignment.status == "pending"
        )
    )
    return {
        "active": active.scalar() or 0,
        "pending": pending.scalar() or 0,
    }


async def assign_task(
    db: AsyncSession,
    mark: str,
    assigned_to: str,
    assigned_by: str,
    project_id: str = "",
    line_item_id: str = "",
    quantity: int = 1,
    total_weight_kg: float = 0,
    drawing_url: str = "",
    notes: str = "",
) -> dict:
    try:
        to_uid = uuid.UUID(assigned_to)
        by_uid = uuid.UUID(assigned_by) if assigned_by else None
        proj_uid = uuid.UUID(project_id) if project_id else None
        li_uid = uuid.UUID(line_item_id) if line_item_id else None
    except ValueError:
        raise ValueError("Invalid UUID")

    emp = await db.get(Employee, to_uid)
    if not emp:
        raise ValueError("Сотрудник не найден")

    deadline = datetime.now(timezone.utc) + timedelta(hours=8)
    deadline_local = deadline + timedelta(hours=7)

    task = TaskAssignment(
        id=uuid.uuid4(),
        project_id=proj_uid,
        line_item_id=li_uid,
        assigned_to=to_uid,
        assigned_by=by_uid,
        mark=mark,
        quantity=quantity,
        total_weight_kg=total_weight_kg,
        drawing_url=drawing_url,
        status=TaskStatus.PENDING,
        deadline=deadline,
        notes=notes,
    )
    db.add(task)
    await db.commit()

    proj = await db.get(Project, proj_uid) if proj_uid else None
    creator = await db.get(Employee, by_uid) if by_uid else None

    deadline_str = deadline_local.strftime("%H:%M (%d.%m.%Y)")

    project_label = f"{proj.name or proj.external_code}" if proj else "Не указан"

    msg_text = (
        f"\U0001f4cc <b>НОВАЯ ЗАДАЧА</b>\n"
        f"\U0001f477 От: {creator.full_name if creator else 'Руководитель'} "
        f"({_role_label(creator.role) if creator else '—'})\n"
        f"\U0001f3d7 Объект: {project_label}\n"
        f"\U0001f9f1 Деталь: Марка {mark} — {quantity} шт.\n"
        f"\u2696\ufe0f Вес: {total_weight_kg} кг\n"
        f"\U0001f4c5 Срок: до {deadline_str}"
    )

    if drawing_url:
        msg_text += f"\n\U0001f4ce Чертеж: {drawing_url}"

    kb = {
        "inline_keyboard": [
            [
                {"text": "\u2705 ПРИНЯТЬ", "callback_data": f"task_accept|{task.id}"},
                {"text": "\u2753 ВОПРОС", "callback_data": f"task_question|{task.id}"},
            ]
        ]
    }

    tg_id = emp.telegram_id
    if tg_id and TELEGRAM_BOT_TOKEN:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": tg_id,
                        "text": msg_text,
                        "parse_mode": "HTML",
                        "reply_markup": kb,
                    },
                )
                if resp.status_code == 200:
                    body = resp.json()
                    if body.get("ok"):
                        task.telegram_msg_id = str(body["result"]["message_id"])
                else:
                    logger.warning("Telegram send failed: %s", resp.text)
        except Exception as exc:
            logger.warning("Telegram send error: %s", exc)

    task.status = TaskStatus.PENDING
    await db.commit()
    await db.refresh(task)

    return _task_to_dict(task)


async def handle_telegram_callback(
    db: AsyncSession,
    callback_data: str,
    telegram_user_id: str,
) -> str:
    try:
        action, task_id = callback_data.split("|", 1)
    except ValueError:
        return "Неверный формат"

    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        return "Задача не найдена"

    result = await db.execute(
        select(TaskAssignment)
        .options(selectinload(TaskAssignment.employee))
        .where(TaskAssignment.id == uid)
    )
    task = result.scalar_one_or_none()
    if not task:
        return "Задача не найдена"

    emp = task.employee
    if emp and emp.telegram_id and str(emp.telegram_id) != str(telegram_user_id):
        return "Эта задача назначена другому сотруднику"

    if action == "task_accept":
        if task.status not in [TaskStatus.PENDING, TaskStatus.QUESTION]:
            return "Задача уже обработана"
        task.status = TaskStatus.ACCEPTED
        task.status_changed_at = datetime.now(timezone.utc)
        await db.commit()
        return "\u2705 Задача принята в работу!"

    elif action == "task_question":
        task.status = TaskStatus.QUESTION
        task.status_changed_at = datetime.now(timezone.utc)
        await db.commit()
        return "\u2753 Вопрос по задаче отправлен руководителю."

    return "Неизвестное действие"


def _role_label(role) -> str:
    labels = {
        "chief_engineer": "Гл. инженер",
        "shop_master": "Нач. участка",
        "worker": "Рабочий",
        "manager": "Менеджер",
        "supply": "Снабжение",
    }
    return labels.get(role.value if hasattr(role, "value") else role, str(role))


def _task_to_dict(t: TaskAssignment) -> dict:
    return {
        "id": str(t.id),
        "project_id": str(t.project_id) if t.project_id else None,
        "line_item_id": str(t.line_item_id) if t.line_item_id else None,
        "assigned_to": str(t.assigned_to),
        "assigned_by": str(t.assigned_by) if t.assigned_by else None,
        "mark": t.mark,
        "quantity": t.quantity,
        "total_weight_kg": float(t.total_weight_kg) if t.total_weight_kg else None,
        "drawing_url": t.drawing_url,
        "status": t.status.value if t.status else "pending",
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "notes": t.notes,
        "telegram_msg_id": t.telegram_msg_id,
        "status_changed_at": t.status_changed_at.isoformat() if t.status_changed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "employee": {
            "id": str(t.employee.id),
            "full_name": t.employee.full_name,
            "role": t.employee.role.value if t.employee.role else "worker",
        } if t.employee else None,
        "project": {
            "id": str(t.project.id),
            "name": t.project.name,
            "external_code": t.project.external_code,
        } if t.project else None,
        "creator": {
            "id": str(t.creator.id),
            "full_name": t.creator.full_name,
        } if t.creator else None,
    }
