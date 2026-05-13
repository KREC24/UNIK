"""Employee API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.employee_service import (
    list_employees, get_employee, create_employee, update_employee, delete_employee,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
async def list_all(db: AsyncSession = Depends(get_db)):
    return await list_employees(db)


@router.get("/{emp_id}")
async def get_one(emp_id: str, db: AsyncSession = Depends(get_db)):
    e = await get_employee(db, emp_id)
    if not e:
        raise HTTPException(404, "Сотрудник не найден")
    return e


@router.post("", status_code=201)
async def create(data: dict, db: AsyncSession = Depends(get_db)):
    return await create_employee(db, data)


@router.put("/{emp_id}")
async def update(emp_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    e = await update_employee(db, emp_id, data)
    if not e:
        raise HTTPException(404, "Сотрудник не найден")
    return e


@router.delete("/{emp_id}", status_code=204)
async def delete(emp_id: str, db: AsyncSession = Depends(get_db)):
    if not await delete_employee(db, emp_id):
        raise HTTPException(404, "Сотрудник не найден")
