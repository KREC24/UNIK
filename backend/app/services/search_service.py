"""Global search service — поиск по проектам, клиентам, загруженным документам."""
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Project, Client, DocumentBatch


async def search_all(db: AsyncSession, query: str) -> dict:
    if not query or len(query.strip()) < 2:
        return {"projects": [], "clients": [], "batches": [], "total": 0}

    q = f"%{query.strip()}%"

    proj_result = await db.execute(
        select(Project)
        .where(
            or_(
                Project.name.ilike(q),
                Project.external_code.ilike(q),
            )
        )
        .order_by(Project.updated_at.desc().nulls_last())
        .limit(6)
    )
    projects = proj_result.scalars().all()

    client_result = await db.execute(
        select(Client)
        .where(
            or_(
                Client.name.ilike(q),
                Client.inn.ilike(q),
            )
        )
        .order_by(Client.created_at.desc())
        .limit(6)
    )
    clients = client_result.scalars().all()

    batch_result = await db.execute(
        select(DocumentBatch)
        .where(DocumentBatch.source_file.ilike(q))
        .order_by(DocumentBatch.created_at.desc())
        .limit(6)
    )
    batches = batch_result.scalars().all()

    return {
        "projects": [
            {
                "id": str(p.id),
                "external_code": p.external_code,
                "name": p.name,
                "stage": p.stage,
            }
            for p in projects
        ],
        "clients": [
            {
                "id": str(c.id),
                "name": c.name,
                "inn": c.inn,
            }
            for c in clients
        ],
        "batches": [
            {
                "batch_id": str(b.id),
                "source_file": b.source_file,
                "batch_type": b.batch_type.value if b.batch_type else "kmd",
                "project_id": str(b.project_id) if b.project_id else None,
            }
            for b in batches
        ],
        "total": len(projects) + len(clients) + len(batches),
    }
