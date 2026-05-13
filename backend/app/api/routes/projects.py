from fastapi import APIRouter, HTTPException

from app.schemas.parser import ProjectCreateSchema, ProjectSchema
from app.services.project_service import get_batch, get_batches_for_project

router = APIRouter(prefix="/projects", tags=["Projects"])

_projects_store: list[dict] = []


@router.get("", response_model=list[ProjectSchema])
async def list_projects():
    return _projects_store


@router.post("", response_model=ProjectSchema)
async def create_project(project: ProjectCreateSchema):
    import uuid
    from datetime import datetime

    new_project = {
        "id": uuid.uuid4(),
        "external_code": project.external_code,
        "name": project.name,
        "stage": project.stage,
        "created_at": datetime.utcnow(),
    }
    _projects_store.append(new_project)
    return new_project


@router.get("/{project_id}")
async def get_project_details(project_id: str):
    project = next((p for p in _projects_store if str(p["id"]) == project_id), None)
    if not project:
        raise HTTPException(404, "Проект не найден")

    batches = get_batches_for_project(project_id)

    return {
        "project": project,
        "batches": batches,
    }
