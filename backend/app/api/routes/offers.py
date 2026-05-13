"""Commercial Offer API routes."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import Project, CommercialOffer, OfferStatus
from app.services.offer_service import generate_offer_pdf, COMPANY_DEFAULTS

router = APIRouter(prefix="/offers", tags=["Commercial Offers"])


@router.post("/generate")
async def generate_offer(
    project_id: str = Query(..., description="UUID проекта"),
    object_name: str = Query("", description="Название объекта (если отличается от имени проекта)"),
    date_str: str = Query("", description="Дата КП (пустая = сегодня)"),
    db: AsyncSession = Depends(get_db),
):
    """Генерирует PDF коммерческого предложения и сохраняет запись в БД."""
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(400, "Некорректный project_id")

    result = await db.execute(
        select(Project).options(selectinload(Project.line_items)).where(Project.id == pid)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Проект не найден")

    obj_name = object_name or project.name or project.external_code or "Объект"
    dt = date_str or ""
    if not dt:
        now = datetime.now(timezone.utc)
        months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        dt = f"от «{now.day} » {months[now.month]} {now.year} г."

    items = []
    total_area = Decimal("0")
    total_weight = Decimal("0")

    if project.line_items:
        for li in project.line_items:
            items.append({
                "n": li.position or 0,
                "name": f"{li.type_name or ''} {li.mark or ''}".strip(),
                "quantity": _fmt_decimal(li.quantity or 0),
                "unit": "шт",
                "price_per_unit": _fmt_price(Decimal("0")),
                "cost_without_vat": _fmt_price(Decimal("0")),
                "vat_amount": _fmt_price(Decimal("0")),
                "cost_with_vat": _fmt_price(Decimal("0")),
            })
            total_area += li.total_area_m2 or Decimal("0")
            total_weight += li.total_weight_kg or Decimal("0")

    pdf_bytes = generate_offer_pdf(
        object_name=obj_name,
        date_str=dt,
        items=items,
    )

    offer = CommercialOffer(
        id=uuid.uuid4(),
        project_id=pid,
        calculated_at=datetime.now(timezone.utc),
        total_area_m2=total_area if total_area > 0 else None,
        total_weight_kg=total_weight if total_weight > 0 else None,
        total_cost=Decimal("0"),
        version=1,
        status=OfferStatus.DRAFT,
    )
    db.add(offer)
    await db.commit()

    filename = f"KP_{obj_name.replace(' ', '_')[:50]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("")
async def list_offers(project_id: str = Query(None), db: AsyncSession = Depends(get_db)):
    """Список КП по проекту."""
    query = select(CommercialOffer)
    if project_id:
        try:
            query = query.where(CommercialOffer.project_id == uuid.UUID(project_id))
        except ValueError:
            raise HTTPException(400, "Некорректный project_id")
    result = await db.execute(query.order_by(CommercialOffer.calculated_at.desc()))
    offers = result.scalars().all()
    return {
        "offers": [
            {
                "id": str(o.id),
                "project_id": str(o.project_id),
                "version": o.version,
                "status": o.status.value if o.status else "draft",
                "total_cost": float(o.total_cost) if o.total_cost else None,
                "calculated_at": o.calculated_at.isoformat() if o.calculated_at else None,
            }
            for o in offers
        ],
        "total": len(offers),
    }


def _fmt_price(value: Decimal) -> str:
    s = f"{value:,.2f}"
    s = s.replace(",", " ").replace(".", ",").replace(" ", "X").replace(",", ".")
    whole, frac = s.split(".")
    whole = whole.replace("X", " ")
    return f"{whole},{frac} ₽"


def _fmt_decimal(value: Decimal) -> str:
    s = f"{value:,.2f}"
    s = s.replace(",", " ").replace(".", ",").replace(" ", "X").replace(",", ".")
    if "." in s:
        whole, frac = s.split(".")
        whole = whole.replace("X", " ")
        return f"{whole},{frac}"
    return s.replace("X", " ")
