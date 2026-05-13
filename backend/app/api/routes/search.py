"""Global search API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.search_service import search_all

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    return await search_all(db, q)
