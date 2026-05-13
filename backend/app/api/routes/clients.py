from fastapi import APIRouter, HTTPException

from app.schemas.parser import ProjectSchema

router = APIRouter(prefix="/clients", tags=["Clients"])

_clients_store: list[dict] = []


@router.get("")
async def list_clients():
    return _clients_store


@router.post("")
async def create_client(client: dict):
    import uuid
    from datetime import datetime

    new_client = {
        "id": str(uuid.uuid4()),
        "name": client.get("name", ""),
        "inn": client.get("inn", ""),
        "contacts": client.get("contacts", {}),
        "created_at": datetime.utcnow().isoformat(),
    }
    _clients_store.append(new_client)
    return new_client


@router.get("/{client_id}")
async def get_client(client_id: str):
    for c in _clients_store:
        if c["id"] == client_id:
            return c
    raise HTTPException(404, "Клиент не найден")
