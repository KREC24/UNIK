"""Incoming requests service — email-based document intake."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    IncomingRequest, IncomingStatus, Client, Project,
)


async def list_incoming(db: AsyncSession, limit: int = 20) -> list[dict]:
    result = await db.execute(
        select(IncomingRequest)
        .options(selectinload(IncomingRequest.client), selectinload(IncomingRequest.project))
        .order_by(IncomingRequest.received_at.desc())
        .limit(limit)
    )
    requests = result.scalars().all()
    return [_incoming_to_dict(r) for r in requests]


async def get_incoming(db: AsyncSession, request_id: str) -> Optional[dict]:
    try:
        uid = uuid.UUID(request_id)
    except ValueError:
        return None
    result = await db.execute(
        select(IncomingRequest)
        .options(selectinload(IncomingRequest.client), selectinload(IncomingRequest.project))
        .where(IncomingRequest.id == uid)
    )
    r = result.scalar_one_or_none()
    return _incoming_to_dict(r) if r else None


async def match_client(db: AsyncSession, request_id: str, client_id: str) -> Optional[dict]:
    try:
        uid = uuid.UUID(request_id)
        cid = uuid.UUID(client_id)
    except ValueError:
        return None

    result = await db.execute(select(IncomingRequest).where(IncomingRequest.id == uid))
    req = result.scalar_one_or_none()
    if not req:
        return None

    client_result = await db.execute(select(Client).where(Client.id == cid))
    client = client_result.scalar_one_or_none()
    if not client:
        return None

    req.client_id = cid
    req.status = IncomingStatus.MATCHED
    req.matched_by = "operator"
    await db.commit()
    await db.refresh(req)
    return _incoming_to_dict(req)


async def process_request(db: AsyncSession, request_id: str) -> Optional[dict]:
    try:
        uid = uuid.UUID(request_id)
    except ValueError:
        return None

    result = await db.execute(
        select(IncomingRequest)
        .options(selectinload(IncomingRequest.client), selectinload(IncomingRequest.project))
        .where(IncomingRequest.id == uid)
    )
    req = result.scalar_one_or_none()
    if not req:
        return None

    if not req.attachments or len(req.attachments) == 0:
        req.status = IncomingStatus.FAILED
        req.error_message = "Нет вложений для обработки"
        await db.commit()
        return _incoming_to_dict(req)

    req.status = IncomingStatus.PROCESSING
    await db.commit()

    from app.services.project_service import find_project, create_project
    from app.schemas.parser import ProjectCreateSchema

    project = None
    if req.client_id:
        projects_result = await db.execute(
            select(Project)
            .where(Project.client_id == req.client_id)
            .order_by(Project.created_at.desc())
            .limit(1)
        )
        project = projects_result.scalar_one_or_none()

    if not project and req.client_id:
        client = await db.get(Client, req.client_id)
        client_name = client.name if client else "Неизвестный"
        project = await create_project(db, ProjectCreateSchema(
            external_code=req.subject or "Входящий",
            name=f"{client_name} — {req.subject or 'Запрос'}",
            stage="КМ",
            client_id=req.client_id,
        ), client_id=req.client_id)

    if not project:
        project = await create_project(db, ProjectCreateSchema(
            external_code=req.subject or "Входящий",
            name=req.subject or "Запрос без клиента",
            stage="КМ",
        ))

    req.project_id = project.id
    req.status = IncomingStatus.PROCESSED
    req.processed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(req)

    return _incoming_to_dict(req)


async def get_incoming_email_address() -> str:
    return "unik@erp.company.ru"


def _incoming_to_dict(r: IncomingRequest) -> dict:
    return {
        "id": str(r.id),
        "sender_email": r.sender_email,
        "sender_name": r.sender_name,
        "subject": r.subject,
        "body_preview": r.body_preview,
        "attachments": r.attachments or [],
        "status": r.status.value if r.status else "pending",
        "matched_by": r.matched_by,
        "result_batch_id": str(r.result_batch_id) if r.result_batch_id else None,
        "error_message": r.error_message,
        "received_at": r.received_at.isoformat() if r.received_at else None,
        "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        "client": {
            "id": str(r.client.id),
            "name": r.client.name,
            "email": r.client.email,
        } if r.client else None,
        "project": {
            "id": str(r.project.id),
            "name": r.project.name,
            "external_code": r.project.external_code,
        } if r.project else None,
    }
