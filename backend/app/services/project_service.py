"""Project service — SQLAlchemy async ORM CRUD + batch persistence."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    Project, DocumentBatch, LineItem, BatchStatus, BatchType, ItemStatus,
)
from app.schemas.parser import ProjectCreateSchema, ProjectUpdateSchema, ParseResultSchema, LineItemSchema


async def find_project(db: AsyncSession, project_id: str) -> Optional[Project]:
    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        return None
    result = await db.execute(
        select(Project).where(Project.id == uid)
    )
    return result.scalar_one_or_none()


async def list_projects(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return list(result.scalars().all())


async def create_project(db: AsyncSession, data: ProjectCreateSchema, client_id: uuid.UUID | None = None) -> Project:
    project = Project(
        id=uuid.uuid4(),
        external_code=data.external_code,
        name=data.name,
        stage=data.stage,
        client_id=client_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(db: AsyncSession, project_id: str, data: ProjectUpdateSchema) -> Optional[Project]:
    project = await find_project(db, project_id)
    if not project:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: str) -> bool:
    project = await find_project(db, project_id)
    if not project:
        return False
    await db.delete(project)
    await db.commit()
    return True


async def assign_client_to_project(db: AsyncSession, project_id: str, client_id: str) -> Optional[dict]:
    project = await find_project(db, project_id)
    if not project:
        return None

    from app.services.clients_service import find_client
    client = await find_client(db, client_id)
    if not client:
        return None

    project.client_id = client.id
    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"project_id": str(project.id), "client_id": str(client.id), "client_name": client.name}


async def get_project_batches(db: AsyncSession, project_id: str) -> list[dict]:
    result = await db.execute(
        select(DocumentBatch)
        .options(selectinload(DocumentBatch.line_items))
        .where(DocumentBatch.project_id == uuid.UUID(project_id))
        .order_by(DocumentBatch.created_at.desc())
    )
    batches = result.scalars().all()
    return [
        {
            "batch_id": str(b.id),
            "source_file": b.source_file,
            "total_items": len(b.line_items) if b.line_items else 0,
            "success_rate": 1.0,
        }
        for b in batches
    ]


async def get_project_line_items(db: AsyncSession, project_id: str) -> list[dict]:
    try:
        uid = uuid.UUID(project_id)
    except ValueError:
        return []
    result = await db.execute(
        select(LineItem).where(LineItem.project_id == uid)
    )
    items = result.scalars().all()
    return [_lineitem_to_dict(li) for li in items]


def _lineitem_to_dict(li: LineItem) -> dict:
    return {
        "batch_id": str(li.batch_id) if li.batch_id else None,
        "position": li.position,
        "mark": li.mark,
        "type_name": li.type_name,
        "quantity": float(li.quantity) if li.quantity else None,
        "length_x": float(li.length_x) if li.length_x else None,
        "width_y": float(li.width_y) if li.width_y else None,
        "height_z": float(li.height_z) if li.height_z else None,
        "unit_weight_kg": float(li.unit_weight_kg) if li.unit_weight_kg else None,
        "total_weight_kg": float(li.total_weight_kg) if li.total_weight_kg else None,
        "unit_area_m2": float(li.unit_area_m2) if li.unit_area_m2 else None,
        "total_area_m2": float(li.total_area_m2) if li.total_area_m2 else None,
        "ptm": float(li.ptm) if li.ptm else None,
        "ogz_notes": li.ogz_notes,
        "profile_type": li.profile_type,
        "steel_grade": li.steel_grade,
        "gost_code": li.gost_code,
    }


async def persist_batch_result(
    db: AsyncSession,
    batch_id: str,
    result: ParseResultSchema,
    project_id: str | None = None,
) -> str:
    """Сохраняет результат парсинга в таблицы document_batches + line_items."""
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        batch_uuid = uuid.uuid4()

    proj_uuid = None
    if project_id:
        try:
            proj_uuid = uuid.UUID(project_id)
        except ValueError:
            proj_uuid = None

    batch_type = BatchType.KMD
    if result.batch_type == "general":
        batch_type = BatchType.GENERAL

    batch = DocumentBatch(
        id=batch_uuid,
        project_id=proj_uuid,
        batch_type=batch_type,
        source_file=result.source_file,
        page_count=0,
        status=BatchStatus.PARSED,
        metadata_json={
            "project_code": result.metadata.project_code,
            "object_name": result.metadata.object_name,
            "stage": result.metadata.stage,
        },
        parsed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(batch)

    for item in result.items:
        _item_to_dec = lambda v, scale=10: Decimal(str(v)).quantize(Decimal("0.1") ** scale) if v is not None else None

        li = LineItem(
            id=uuid.uuid4(),
            batch_id=batch_uuid,
            project_id=proj_uuid,
            source_sheet=result.source_file,
            position=item.position,
            mark=item.mark,
            type_name=item.type_name,
            quantity=item.quantity,
            length_x=item.length_x,
            width_y=item.width_y,
            height_z=item.height_z,
            unit_weight_kg=item.unit_weight_kg,
            total_weight_kg=item.total_weight_kg,
            unit_area_m2=item.unit_area_m2,
            total_area_m2=item.total_area_m2,
            ptm=item.ptm,
            ogz_notes=item.ogz_notes,
            profile_type=item.profile_type,
            steel_grade=item.steel_grade,
            gost_code=item.gost_code,
            status=ItemStatus.RAW,
            parse_confidence=item.confidence,
        )
        db.add(li)

    for row in result.unrecognized_rows:
        li = LineItem(
            id=uuid.uuid4(),
            batch_id=batch_uuid,
            project_id=proj_uuid,
            status=ItemStatus.REJECTED,
            raw_text=row.raw_text,
            parse_confidence=0.0,
        )
        db.add(li)

    await db.commit()
    return str(batch_uuid)


async def get_batch_from_db(db: AsyncSession, batch_id: str) -> Optional[dict]:
    """Получить пакет + все строки из БД."""
    try:
        uid = uuid.UUID(batch_id)
    except ValueError:
        return None

    result = await db.execute(
        select(DocumentBatch).where(DocumentBatch.id == uid)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        return None

    items_result = await db.execute(
        select(LineItem).where(LineItem.batch_id == uid)
    )
    items = items_result.scalars().all()

    return {
        "batch_id": str(batch.id),
        "source_file": batch.source_file,
        "status": batch.status.value if batch.status else "parsed",
        "total_items": len([it for it in items if it.status != ItemStatus.REJECTED]),
        "items": [_lineitem_to_dict(it) for it in items if it.status != ItemStatus.REJECTED],
        "unrecognized_count": len([it for it in items if it.status == ItemStatus.REJECTED]),
        "unrecognized_rows": [
            {"raw_text": it.raw_text, "partial_data": {}, "issues": []}
            for it in items if it.status == ItemStatus.REJECTED
        ],
        "total_rows_parsed": len([it for it in items if it.status != ItemStatus.REJECTED]),
        "total_rows_raw": len(items),
        "success_rate": len([it for it in items if it.status != ItemStatus.REJECTED]) / max(len(items), 1),
        "errors": [],
        "metadata": batch.metadata_json or {},
        "batch_type": batch.batch_type.value if batch.batch_type else "kmd",
    }
