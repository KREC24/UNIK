"""Incoming requests API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.incoming_service import (
    list_incoming,
    get_incoming,
    match_client,
    process_request,
    get_incoming_email_address,
)

router = APIRouter(prefix="/incoming", tags=["Incoming"])


@router.get("/email")
async def incoming_email():
    return {"email": get_incoming_email_address()}


@router.get("")
async def list_requests(db: AsyncSession = Depends(get_db)):
    return await list_incoming(db)


@router.get("/{request_id}")
async def get_request(request_id: str, db: AsyncSession = Depends(get_db)):
    req = await get_incoming(db, request_id)
    if not req:
        raise HTTPException(404, "Запрос не найден")
    return req


@router.post("/{request_id}/match")
async def match_request(request_id: str, client_id: str, db: AsyncSession = Depends(get_db)):
    req = await match_client(db, request_id, client_id)
    if not req:
        raise HTTPException(404, "Запрос или клиент не найден")
    return req


@router.post("/{request_id}/process")
async def process_incoming(request_id: str, db: AsyncSession = Depends(get_db)):
    req = await process_request(db, request_id)
    if not req:
        raise HTTPException(404, "Запрос не найден")
    return req
