import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query

from app.schemas.ogz import (
    OgzCalculationRequest,
    OgzCalculationResponse,
    OgzCompositionSchema,
    OgzCompositionCreateRequest,
)
from app.services.ogz_service import calculate_ogz

router = APIRouter(prefix="/ogz", tags=["OGZ Calculator"])

_default_compositions: list[dict] = []


def _ensure_defaults():
    """Заполняет справочник значениями по умолчанию при первом обращении."""
    if not _default_compositions:
        _default_compositions.extend([
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
                "name": "Грунт ГФ-021",
                "composition_type": "grunt",
                "consumption_rate": Decimal("0.30"),
                "price_per_kg": Decimal("500.00"),
                "dry_residue": Decimal("55.0"),
                "density": Decimal("1.40"),
                "min_ptm_mm": Decimal("1.00"),
                "max_ptm_mm": Decimal("50.00"),
                "rei_minutes": 60,
                "environment": "сухая",
            },
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
                "name": "Краска Термобарьер",
                "composition_type": "kraska",
                "consumption_rate": Decimal("0.90"),
                "price_per_kg": Decimal("1200.00"),
                "dry_residue": Decimal("65.0"),
                "density": Decimal("1.50"),
                "min_ptm_mm": Decimal("1.00"),
                "max_ptm_mm": Decimal("50.00"),
                "rei_minutes": 60,
                "environment": "сухая",
            },
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
                "name": "Финиш ПФ-115",
                "composition_type": "finish",
                "consumption_rate": Decimal("0.25"),
                "price_per_kg": Decimal("400.00"),
                "dry_residue": Decimal("50.0"),
                "density": Decimal("1.20"),
                "min_ptm_mm": Decimal("1.00"),
                "max_ptm_mm": Decimal("50.00"),
                "rei_minutes": 60,
                "environment": "сухая",
            },
        ])


def _composition_to_dict(c: dict) -> dict:
    return {
        "id": str(c["id"]),
        "name": c["name"],
        "composition_type": c["composition_type"],
        "consumption_rate": float(c["consumption_rate"]) if c.get("consumption_rate") else None,
        "price_per_kg": float(c["price_per_kg"]) if c.get("price_per_kg") else None,
        "dry_residue": float(c["dry_residue"]) if c.get("dry_residue") else None,
        "density": float(c["density"]) if c.get("density") else None,
        "min_ptm_mm": float(c["min_ptm_mm"]) if c.get("min_ptm_mm") else None,
        "max_ptm_mm": float(c["max_ptm_mm"]) if c.get("max_ptm_mm") else None,
        "rei_minutes": c.get("rei_minutes"),
        "environment": c.get("environment"),
    }


@router.post("/calculate", response_model=OgzCalculationResponse)
async def ogz_calculate(request: OgzCalculationRequest):
    """Расчёт спецификации ОГЗ-материалов."""
    if not request.items and not request.line_item_ids:
        raise HTTPException(400, "Передайте items или line_item_ids для расчёта")

    if request.rei < 15 or request.rei > 240:
        raise HTTPException(400, "REI должен быть от 15 до 240 минут")

    if request.environment not in ("сухая", "влажная", "агрессивная"):
        raise HTTPException(400, "Среда должна быть: сухая, влажная или агрессивная")

    _ensure_defaults()
    response = calculate_ogz(request, compositions=_default_compositions)
    return response


@router.get("/compositions")
async def ogz_list_compositions(
    composition_type: str = Query(None, description="grunt | kraska | finish"),
    rei_minutes: int = Query(None, description="Предел огнестойкости"),
    environment: str = Query(None, description="Среда: сухая/влажная/агрессивная"),
):
    """Получить справочник ОГЗ-составов с возможностью фильтрации."""
    _ensure_defaults()

    comps = _default_compositions
    if composition_type:
        comps = [c for c in comps if c["composition_type"] == composition_type]
    if rei_minutes:
        comps = [c for c in comps if c.get("rei_minutes") == rei_minutes]
    if environment:
        comps = [c for c in comps if (c.get("environment") or "").lower() == environment.lower()]

    return {
        "compositions": [_composition_to_dict(c) for c in comps],
        "total": len(comps),
    }


@router.post("/compositions", status_code=201)
async def ogz_add_composition(request: OgzCompositionCreateRequest):
    """Добавить новый состав в справочник."""
    _ensure_defaults()

    if request.composition_type not in ("grunt", "kraska", "finish"):
        raise HTTPException(400, "composition_type должен быть: grunt, kraska или finish")

    new_id = uuid.uuid4()
    new_comp = {
        "id": new_id,
        "name": request.name,
        "composition_type": request.composition_type,
        "consumption_rate": request.consumption_rate or Decimal("0"),
        "price_per_kg": request.price_per_kg or Decimal("0"),
        "dry_residue": request.dry_residue,
        "density": request.density,
        "min_ptm_mm": request.min_ptm_mm,
        "max_ptm_mm": request.max_ptm_mm,
        "rei_minutes": request.rei_minutes,
        "environment": request.environment,
    }
    _default_compositions.append(new_comp)

    return _composition_to_dict(new_comp)
