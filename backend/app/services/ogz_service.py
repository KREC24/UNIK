"""
Бизнес-логика расчёта огнезащиты металлоконструкций.

Оркестрирует:
  - загрузку справочника ogz_compositions (из БД или in-memory)
  - вызов ogz_calculator.calculate_ogz_full
  - формирование OgzCalculationResponse
"""
import logging
from decimal import Decimal

from app.core.ogz_calculator import (
    calculate_ogz_full,
    FullCalculation,
    CompositionRecord,
)
from app.schemas.ogz import (
    OgzCalculationRequest,
    OgzCalculationResponse,
    OgzCalculationTotals,
    OgzCompositionInfo,
    OgzPositionResult,
)
from app.schemas.parser import LineItemSchema

logger = logging.getLogger(__name__)


def _item_to_dict(item: LineItemSchema | dict) -> dict:
    """Преобразует LineItemSchema или словарь в словарь для ядра расчёта."""
    if isinstance(item, dict):
        return {
            "mark": item.get("mark"),
            "type_name": item.get("type_name"),
            "quantity": item.get("quantity", 1) or 1,
            "unit_weight_kg": item.get("unit_weight_kg") or Decimal("0"),
            "total_weight_kg": item.get("total_weight_kg") or Decimal("0"),
            "unit_area_m2": item.get("unit_area_m2") or Decimal("0"),
            "total_area_m2": item.get("total_area_m2") or Decimal("0"),
            "ptm": item.get("ptm"),
        }
    return {
        "mark": item.mark,
        "type_name": item.type_name,
        "quantity": item.quantity or Decimal("1"),
        "unit_weight_kg": item.unit_weight_kg or Decimal("0"),
        "total_weight_kg": item.total_weight_kg or Decimal("0"),
        "unit_area_m2": item.unit_area_m2 or Decimal("0"),
        "total_area_m2": item.total_area_m2 or Decimal("0"),
        "ptm": item.ptm,
    }


def _compositions_to_records(compositions: list[dict]) -> list[CompositionRecord]:
    """Преобразует словари справочника в CompositionRecord."""
    records: list[CompositionRecord] = []
    for c in compositions:
        records.append(CompositionRecord(
            name=c.get("name", ""),
            composition_type=c.get("composition_type", ""),
            consumption_rate=c.get("consumption_rate"),
            price_per_kg=c.get("price_per_kg"),
            dry_residue=c.get("dry_residue"),
            density=c.get("density"),
            min_ptm_mm=c.get("min_ptm_mm"),
            max_ptm_mm=c.get("max_ptm_mm"),
            rei_minutes=c.get("rei_minutes"),
            environment=c.get("environment"),
        ))
    return records


def calculate_ogz(
    request: OgzCalculationRequest,
    items_data: list[LineItemSchema] | None = None,
    compositions: list[dict] | None = None,
) -> OgzCalculationResponse:
    """
    Выполняет полный расчёт ОГЗ по переданным позициям.

    Args:
        request: запрос с параметрами REI, среды и списком items/line_item_ids
        items_data: опциональный список LineItemSchema
        compositions: опциональный справочник ОГЗ-составов

    Returns:
        OgzCalculationResponse со спецификацией материалов и итогами
    """
    items_for_calc: list[dict] = []

    if request.items:
        for inp in request.items:
            weight = inp.total_weight_kg or inp.unit_weight_kg or Decimal("0")
            area = inp.total_area_m2 or inp.unit_area_m2 or Decimal("0")
            items_for_calc.append({
                "mark": inp.mark,
                "type_name": inp.type_name,
                "quantity": inp.quantity,
                "unit_weight_kg": inp.unit_weight_kg or Decimal("0"),
                "total_weight_kg": weight,
                "unit_area_m2": inp.unit_area_m2 or Decimal("0"),
                "total_area_m2": area,
                "ptm": inp.ptm,
            })

    if items_data:
        for item in items_data:
            items_for_calc.append(_item_to_dict(item))

    if not items_for_calc:
        return OgzCalculationResponse(errors=["Нет позиций для расчёта — передайте items или items_data"])

    comps = compositions or []
    records = _compositions_to_records(comps)

    result: FullCalculation = calculate_ogz_full(
        items=items_for_calc,
        compositions=records,
        rei_minutes=request.rei,
        environment=request.environment,
    )

    positions = [
        OgzPositionResult(
            mark=p.mark,
            type_name=p.type_name,
            quantity=p.quantity,
            unit_weight_kg=p.unit_weight_kg,
            unit_area_m2=p.unit_area_m2,
            reduced_thickness_mm=p.reduced_thickness_mm,
            matched_composition_name=p.matched_composition_name,
            grunt_consumption_kg=p.grunt_consumption_kg,
            kraska_consumption_kg=p.kraska_consumption_kg,
            finish_consumption_kg=p.finish_consumption_kg,
            position_cost_rub=p.position_cost_rub,
            verification_warnings=p.verification_warnings,
        )
        for p in result.positions
    ]

    totals = OgzCalculationTotals(**result.totals)

    comp_info = OgzCompositionInfo(**result.composition) if result.composition.get("grunt_name") or result.composition.get("kraska_name") else None

    return OgzCalculationResponse(
        positions=positions,
        totals=totals,
        composition=comp_info,
        errors=result.errors,
    )
