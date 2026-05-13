"""Project API routes — async ORM."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.parser import ProjectCreateSchema, ProjectUpdateSchema
from app.services.project_service import (
    list_projects as svc_list,
    find_project as svc_find,
    create_project as svc_create,
    update_project as svc_update,
    delete_project as svc_delete,
    assign_client_to_project as svc_assign,
    get_project_batches as svc_batches,
    get_project_line_items as svc_items,
)
from app.services.clients_service import find_client as svc_find_client

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_to_dict(p) -> dict:
    return {
        "id": str(p.id),
        "external_code": p.external_code,
        "name": p.name,
        "stage": p.stage,
        "client_id": str(p.client_id) if p.client_id else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    projects = await svc_list(db)
    return [_project_to_dict(p) for p in projects]


@router.post("", status_code=201)
async def create_project(data: ProjectCreateSchema, db: AsyncSession = Depends(get_db)):
    client_id = data.client_id
    if client_id and not await svc_find_client(db, str(client_id)):
        raise HTTPException(404, "Клиент не найден")
    project = await svc_create(db, data, client_id)
    return _project_to_dict(project)


@router.get("/{project_id}")
async def get_project_details(project_id: str, db: AsyncSession = Depends(get_db)):
    import traceback
    try:
        project = await svc_find(db, project_id)
        if not project:
            raise HTTPException(404, "Проект не найден")
        batches = await svc_batches(db, project_id)
        items = await svc_items(db, project_id)
        return {
            "project": _project_to_dict(project),
            "batches": batches,
            "items": items,
            "items_count": len(items),
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@router.put("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdateSchema, db: AsyncSession = Depends(get_db)):
    if data.client_id and not await svc_find_client(db, str(data.client_id)):
        raise HTTPException(404, "Клиент не найден")
    project = await svc_update(db, project_id, data)
    if not project:
        raise HTTPException(404, "Проект не найден")
    return _project_to_dict(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    if not await svc_delete(db, project_id):
        raise HTTPException(404, "Проект не найден")


@router.put("/{project_id}/assign-client")
async def assign_client(project_id: str, client_id: str, db: AsyncSession = Depends(get_db)):
    result = await svc_assign(db, project_id, client_id)
    if not result:
        raise HTTPException(404, "Проект или клиент не найден")
    return result


@router.get("/{project_id}/items")
async def list_project_items(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await svc_find(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    items = await svc_items(db, project_id)
    return {"project_id": project_id, "items": items, "total": len(items)}


@router.get("/{project_id}/offers")
async def list_project_offers(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await svc_find(db, project_id)
    if not project:
        raise HTTPException(404, "Проект не найден")
    offers = project.commercial_offers or []
    return {
        "project_id": project_id,
        "offers": [
            {
                "id": str(o.id),
                "version": o.version,
                "status": o.status.value if o.status else "draft",
                "total_cost": float(o.total_cost) if o.total_cost else None,
                "calculated_at": o.calculated_at.isoformat() if o.calculated_at else None,
            }
            for o in offers
        ],
        "total": len(offers),
    }
