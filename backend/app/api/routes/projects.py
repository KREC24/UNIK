from fastapi import APIRouter

from app.schemas.parser import ProjectCreateSchema, ProjectSchema

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
