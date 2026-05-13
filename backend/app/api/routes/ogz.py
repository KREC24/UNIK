"""OGZ Calculator API routes — DB-backed."""
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import OgzComposition
from app.schemas.ogz import (
    OgzCalculationRequest,
    OgzCalculationResponse,
    OgzCompositionCreateRequest,
)
from app.services.ogz_service import calculate_ogz
from app.config import get_default_environment

router = APIRouter(prefix="/ogz", tags=["OGZ Calculator"])


async def _get_compositions(db: AsyncSession) -> list[dict]:
    """Load all compositions from DB. Seeds defaults if empty."""
    result = await db.execute(select(OgzComposition))
    comps = list(result.scalars().all())

    if not comps:
        comps = await _seed_defaults(db)
        result = await db.execute(select(OgzComposition))
        comps = list(result.scalars().all())

    return [_composition_to_dict(c) for c in comps]


async def _seed_defaults(db: AsyncSession) -> list[OgzComposition]:
    defaults = [
        OgzComposition(
            id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
            name="Грунт ГФ-021", composition_type="grunt",
            consumption_rate=Decimal("0.30"), price_per_kg=Decimal("500.00"),
            dry_residue=Decimal("55.0"), density=Decimal("1.40"),
            min_ptm_mm=Decimal("1.00"), max_ptm_mm=Decimal("50.00"),
        ),
        OgzComposition(
            id=uuid.UUID("a0000000-0000-0000-0000-000000000002"),
            name="Краска Термобарьер", composition_type="kraska",
            consumption_rate=Decimal("0.90"), price_per_kg=Decimal("1200.00"),
            dry_residue=Decimal("65.0"), density=Decimal("1.50"),
            min_ptm_mm=Decimal("1.00"), max_ptm_mm=Decimal("50.00"),
        ),
        OgzComposition(
            id=uuid.UUID("a0000000-0000-0000-0000-000000000003"),
            name="Финиш ПФ-115", composition_type="finish",
            consumption_rate=Decimal("0.25"), price_per_kg=Decimal("400.00"),
            dry_residue=Decimal("50.0"), density=Decimal("1.20"),
            min_ptm_mm=Decimal("1.00"), max_ptm_mm=Decimal("50.00"),
        ),
    ]
    for c in defaults:
        db.add(c)
    await db.commit()
    return defaults


def _composition_to_dict(c: OgzComposition) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "composition_type": c.composition_type,
        "consumption_rate": float(c.consumption_rate) if c.consumption_rate else None,
        "price_per_kg": float(c.price_per_kg) if c.price_per_kg else None,
        "dry_residue": float(c.dry_residue) if c.dry_residue else None,
        "density": float(c.density) if c.density else None,
        "min_ptm_mm": float(c.min_ptm_mm) if c.min_ptm_mm else None,
        "max_ptm_mm": float(c.max_ptm_mm) if c.max_ptm_mm else None,
        "rei_minutes": c.rei_minutes,
        "environment": c.environment,
    }


@router.post("/calculate", response_model=OgzCalculationResponse)
async def ogz_calculate(request: OgzCalculationRequest, db: AsyncSession = Depends(get_db)):
    if not request.items and not request.line_item_ids:
        raise HTTPException(400, "Передайте items или line_item_ids для расчёта")

    if request.rei < 15 or request.rei > 240:
        raise HTTPException(400, "REI должен быть от 15 до 240 минут")

    env = request.environment or get_default_environment()
    if env not in ("сухая", "влажная", "агрессивная"):
        raise HTTPException(400, "Среда должна быть: сухая, влажная или агрессивная")

    request.environment = env

    compositions = await _get_compositions(db)
    response = calculate_ogz(request, compositions=compositions)
    return response


@router.get("/compositions")
async def ogz_list_compositions(
    composition_type: str = Query(None, description="grunt | kraska | finish"),
    rei_minutes: int = Query(None, description="Предел огнестойкости"),
    environment: str = Query(None, description="Среда: сухая/влажная/агрессивная"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OgzComposition).order_by(OgzComposition.name))
    comps = list(result.scalars().all())

    if composition_type:
        comps = [c for c in comps if c.composition_type == composition_type]
    if rei_minutes:
        comps = [c for c in comps if c.rei_minutes == rei_minutes]
    if environment:
        comps = [c for c in comps if (c.environment or "").lower() == environment.lower()]

    return {
        "compositions": [_composition_to_dict(c) for c in comps],
        "total": len(comps),
    }


@router.post("/compositions", status_code=201)
async def ogz_add_composition(request: OgzCompositionCreateRequest, db: AsyncSession = Depends(get_db)):
    if request.composition_type not in ("grunt", "kraska", "finish"):
        raise HTTPException(400, "composition_type должен быть: grunt, kraska или finish")

    comp = OgzComposition(
        id=uuid.uuid4(),
        name=request.name,
        composition_type=request.composition_type,
        consumption_rate=request.consumption_rate or Decimal("0"),
        price_per_kg=request.price_per_kg or Decimal("0"),
        dry_residue=request.dry_residue,
        density=request.density,
        min_ptm_mm=request.min_ptm_mm,
        max_ptm_mm=request.max_ptm_mm,
        rei_minutes=request.rei_minutes,
        environment=request.environment,
    )
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return _composition_to_dict(comp)
