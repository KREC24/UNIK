"""Client API routes — async ORM."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.parser import ClientCreateSchema, ClientUpdateSchema
from app.services.clients_service import (
    list_clients as svc_list,
    find_client as svc_find,
    create_client as svc_create,
    update_client as svc_update,
    delete_client as svc_delete,
    get_client_projects as svc_projects,
)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("")
async def list_clients(db: AsyncSession = Depends(get_db)):
    clients = await svc_list(db)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "inn": c.inn,
            "contacts": c.contacts,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in clients
    ]


@router.post("", status_code=201)
async def create_client_endpoint(data: ClientCreateSchema, db: AsyncSession = Depends(get_db)):
    client = await svc_create(db, data)
    return {
        "id": str(client.id),
        "name": client.name,
        "inn": client.inn,
        "contacts": client.contacts,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


@router.get("/{client_id}")
async def get_client(client_id: str, db: AsyncSession = Depends(get_db)):
    client = await svc_find(db, client_id)
    if not client:
        raise HTTPException(404, "Клиент не найден")
    return {
        "id": str(client.id),
        "name": client.name,
        "inn": client.inn,
        "contacts": client.contacts,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


@router.put("/{client_id}")
async def update_client_endpoint(client_id: str, data: ClientUpdateSchema, db: AsyncSession = Depends(get_db)):
    client = await svc_update(db, client_id, data)
    if not client:
        raise HTTPException(404, "Клиент не найден")
    return {
        "id": str(client.id),
        "name": client.name,
        "inn": client.inn,
        "contacts": client.contacts,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


@router.delete("/{client_id}", status_code=204)
async def delete_client_endpoint(client_id: str, db: AsyncSession = Depends(get_db)):
    if not await svc_delete(db, client_id):
        raise HTTPException(404, "Клиент не найден")


@router.get("/{client_id}/projects")
async def list_client_projects(client_id: str, db: AsyncSession = Depends(get_db)):
    c = await svc_find(db, client_id)
    if not c:
        raise HTTPException(404, "Клиент не найден")
    projects = await svc_projects(db, client_id)
    return {
        "client_id": client_id,
        "client_name": c.name,
        "projects": projects,
        "total": len(projects),
    }
