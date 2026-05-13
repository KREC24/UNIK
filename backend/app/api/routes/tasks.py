"""Task assignment + Telegram bot API routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.task_service import (
    list_tasks, get_task_stats, assign_task, handle_telegram_callback,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("")
async def list_all(status: str = "", db: AsyncSession = Depends(get_db)):
    return await list_tasks(db, status)


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    return await get_task_stats(db)


@router.post("/assign")
async def create_task(data: dict, db: AsyncSession = Depends(get_db)):
    try:
        return await assign_task(
            db,
            mark=data["mark"],
            assigned_to=data["assigned_to"],
            assigned_by=data.get("assigned_by", ""),
            project_id=data.get("project_id", ""),
            line_item_id=data.get("line_item_id", ""),
            quantity=data.get("quantity", 1),
            total_weight_kg=data.get("total_weight_kg", 0),
            drawing_url=data.get("drawing_url", ""),
            notes=data.get("notes", ""),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/telegram-webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    if "callback_query" in body:
        cq = body["callback_query"]
        user_id = str(cq["from"]["id"])
        data = cq.get("data", "")
        msg = await handle_telegram_callback(db, data, user_id)
        return {"method": "answerCallbackQuery", "callback_query_id": cq["id"], "text": msg}
    return {"ok": True}
