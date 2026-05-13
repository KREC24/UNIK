"""Dashboard service — aggregated statistics for the main page."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    Project, DocumentBatch, LineItem, BatchStatus, ItemStatus,
)


async def get_dashboard_stats(db: AsyncSession) -> dict:
    projects_result = await db.execute(select(func.count(Project.id)))
    total_projects = projects_result.scalar() or 0

    weight_result = await db.execute(
        select(func.coalesce(func.sum(LineItem.total_weight_kg), 0)).where(
            LineItem.status != ItemStatus.REJECTED
        )
    )
    total_weight_kg = float(weight_result.scalar() or 0)

    area_result = await db.execute(
        select(func.coalesce(func.sum(LineItem.total_area_m2), 0)).where(
            LineItem.status != ItemStatus.REJECTED
        )
    )
    total_area_m2 = float(area_result.scalar() or 0)

    items_count_result = await db.execute(
        select(func.count(LineItem.id)).where(
            LineItem.status != ItemStatus.REJECTED
        )
    )
    total_items = items_count_result.scalar() or 0

    batches_result = await db.execute(
        select(DocumentBatch)
        .options(selectinload(DocumentBatch.project))
        .order_by(DocumentBatch.created_at.desc())
        .limit(5)
    )
    batches = batches_result.scalars().all()

    recent_files = []
    for b in batches:
        items_result = await db.execute(
            select(func.count(LineItem.id)).where(
                LineItem.batch_id == b.id,
                LineItem.status != ItemStatus.REJECTED,
            )
        )
        items_count = items_result.scalar() or 0

        recent_files.append({
            "batch_id": str(b.id),
            "source_file": b.source_file,
            "batch_type": b.batch_type.value if b.batch_type else "kmd",
            "status": b.status.value if b.status else "parsed",
            "total_items": items_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "project_name": b.project.name if b.project else None,
            "project_id": str(b.project.id) if b.project else None,
        })

    return {
        "total_projects": total_projects,
        "total_weight_kg": round(total_weight_kg, 1),
        "total_area_m2": round(total_area_m2, 2),
        "total_items": total_items,
        "recent_files": recent_files,
    }
