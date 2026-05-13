"""
Ядро расчёта огнезащиты металлоконструкций.

Алгоритм «Калькулятор ОГЗ»:
  1. Для каждой позиции рассчитывается PTM = M / (S × 7.85) [мм]
  2. По PTM и параметрам (REI, среда) из справочника ogz_compositions подбирается:
     - Грунт (grunt): фильтр min_ptm <= PTM <= max_ptm, REI, среда
     - Краска (kraska): тот же фильтр по PTM
     - Финиш (finish): тот же фильтр
  3. Расход:
     R_грунт  = S_общ × N_грунт         [кг]
     R_краска = S_общ × PTM × N_краска   [кг]
     R_финиш  = S_общ × N_финиш         [кг]
  4. Проверка (verification):
     При наличии dry_residue (%) и density (г/см³) проверяется,
     что заложенный consumption_rate обеспечивает требуемую толщину
     сухой плёнки: DFT_достиг = rate × dry_residue / (density × 10) [мм]
  5. Стоимость = Σ(R_i × price_i)
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

STEEL_DENSITY = Decimal("7850")
STEEL_DENSITY_MM = Decimal("7.85")

REI_AVAILABLE = [30, 60, 90, 120, 150]


@dataclass
class CompositionRecord:
    """Запись из справочника ogz_compositions (словарь или ORM-объект)."""
    name: str
    composition_type: str
    consumption_rate: Optional[Decimal] = None
    price_per_kg: Optional[Decimal] = None
    dry_residue: Optional[Decimal] = None
    density: Optional[Decimal] = None
    min_ptm_mm: Optional[Decimal] = None
    max_ptm_mm: Optional[Decimal] = None
    rei_minutes: Optional[int] = None
    environment: Optional[str] = None


@dataclass
class PositionCalculation:
    """Результат расчёта по одной позиции."""
    mark: Optional[str] = None
    type_name: Optional[str] = None
    quantity: int = 1
    unit_weight_kg: float = 0.0
    unit_area_m2: float = 0.0
    reduced_thickness_mm: float = 0.0
    matched_composition_id: Optional[str] = None
    matched_composition_name: Optional[str] = None
    grunt_consumption_kg: float = 0.0
    kraska_consumption_kg: float = 0.0
    finish_consumption_kg: float = 0.0
    position_cost_rub: float = 0.0
    verification_warnings: list[str] = field(default_factory=list)


@dataclass
class FullCalculation:
    """Полный результат расчёта ОГЗ."""
    positions: list[PositionCalculation] = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    composition: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# PTM
# ---------------------------------------------------------------------------

def calculate_reduced_thickness(mass_kg: Decimal | float, area_m2: Decimal | float) -> Decimal:
    """δ_пр = M / (S × 7.85)  [мм]"""
    try:
        m = Decimal(str(mass_kg))
        a = Decimal(str(area_m2))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")
    if a == 0:
        return Decimal("0")
    return (m / (a * STEEL_DENSITY_MM)).quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Подбор состава из справочника
# ---------------------------------------------------------------------------

def _to_dec(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _composition_matches_ptm(comp: CompositionRecord, ptm: Decimal) -> bool:
    if comp.min_ptm_mm is None and comp.max_ptm_mm is None:
        return True
    lo = _to_dec(comp.min_ptm_mm) or Decimal("-Infinity")
    hi = _to_dec(comp.max_ptm_mm) or Decimal("Infinity")
    return lo <= ptm <= hi


def _nearest_rei(rei: int) -> int:
    return min(REI_AVAILABLE, key=lambda r: abs(r - rei))


def match_compositions(
    compositions: list[CompositionRecord],
    ptm: Decimal | float,
    rei_minutes: int,
    environment: str,
) -> dict[str, CompositionRecord]:
    """
    Подбирает составы (grunt, kraska, finish) из справочника по PTM, REI, среде.

    Возвращает словарь {"grunt": ..., "kraska": ..., "finish": ...}.
    Если для какого-то типа не найдено — остаются None.
    """
    ptm_dec = Decimal(str(ptm))
    env = environment.lower() if environment else "сухая"
    nearest = _nearest_rei(rei_minutes)

    matched: dict[str, CompositionRecord] = {}

    for comp_type in ("grunt", "kraska", "finish"):
        candidates = [
            c for c in compositions
            if c.composition_type == comp_type
            and _composition_matches_ptm(c, ptm_dec)
            and (c.rei_minutes is None or c.rei_minutes == nearest)
            and (c.environment is None or c.environment.lower() == env)
        ]
        if candidates:
            candidates.sort(
                key=lambda c: (_to_dec(c.min_ptm_mm) or Decimal("9999"))
            )
            matched[comp_type] = candidates[0]

    return matched


# ---------------------------------------------------------------------------
# Верификация (dry_residue + density)
# ---------------------------------------------------------------------------

def verify_consumption_rate(comp: CompositionRecord, ptm_mm: Decimal) -> list[str]:
    """
    Проверяет корректность consumption_rate по dry_residue и density.

    Формула: DFT_достиг = rate × dry_residue / (density × 10)  [мм]

    Для грунта/финиша: DFT должна быть >= 0.05 мм (типовой минимум).
    Для краски: DFT_достиг должна быть >= PTM × 0.5 (эмпирический порог).
    Возвращает список предупреждений.
    """
    warnings: list[str] = []
    rate = _to_dec(comp.consumption_rate)
    dr = _to_dec(comp.dry_residue)
    dens = _to_dec(comp.density)

    if rate is None or dr is None or dens is None:
        return warnings

    if dr == 0 or dens == 0:
        return warnings

    achieved_dft = rate * dr / (dens * Decimal("10"))

    if comp.composition_type in ("grunt", "finish"):
        min_dft = Decimal("0.05")
        if achieved_dft < min_dft:
            warnings.append(
                f"{comp.name}: достигнутая DFT={float(achieved_dft):.3f} мм "
                f"ниже минимальной {float(min_dft)} мм. "
                f"Увеличьте consumption_rate до ≥ {float(min_dft * dens * 10 / dr):.2f} кг/м²"
            )
    elif comp.composition_type == "kraska":
        ptm = Decimal(str(ptm_mm))
        min_dft = ptm * Decimal("0.5")
        if achieved_dft < min_dft:
            warnings.append(
                f"{comp.name}: достигнутая DFT={float(achieved_dft):.3f} мм "
                f"ниже требуемой {float(min_dft):.3f} мм (PTM×0.5). "
                f"Увеличьте consumption_rate до ≥ {float(min_dft * dens * 10 / dr):.2f} кг/м²"
            )

    return warnings


# ---------------------------------------------------------------------------
# Полный расчёт
# ---------------------------------------------------------------------------

def calculate_ogz_full(
    items: list[dict],
    compositions: list[CompositionRecord],
    rei_minutes: int,
    environment: str,
) -> FullCalculation:
    """
    Полный расчёт ОГЗ по позициям с подбором состава из справочника.

    Args:
        items: список словарей с полями:
            mark, type_name, quantity,
            unit_weight_kg, total_weight_kg,
            unit_area_m2, total_area_m2, ptm (опционально)
        compositions: записи из справочника ogz_compositions
        rei_minutes: предел огнестойкости (30..150)
        environment: среда (сухая/влажная/агрессивная)

    Returns:
        FullCalculation с позициями, итогами, подобранным составом
    """
    errors: list[str] = []
    positions: list[PositionCalculation] = []

    total_area = Decimal("0")
    total_weight = Decimal("0")
    total_quantity = 0
    grunt_total = Decimal("0")
    kraska_total = Decimal("0")
    finish_total = Decimal("0")
    cost_total = Decimal("0")

    composition_info: dict = {
        "rei_minutes": _nearest_rei(rei_minutes),
        "environment": environment,
    }

    for item in items:
        qty = int(item.get("quantity", 1) or 1)
        weight = Decimal(str(item.get("total_weight_kg") or item.get("unit_weight_kg") or 0))
        area = Decimal(str(item.get("total_area_m2") or item.get("unit_area_m2") or 0))
        ptm_raw = item.get("ptm")

        if ptm_raw is not None:
            try:
                ptm = Decimal(str(ptm_raw))
            except (InvalidOperation, ValueError, TypeError):
                ptm = calculate_reduced_thickness(weight, area)
        else:
            ptm = calculate_reduced_thickness(weight, area)

        matched = match_compositions(compositions, ptm, rei_minutes, environment)

        grunt = matched.get("grunt")
        kraska = matched.get("kraska")
        finish = matched.get("finish")

        verification_warnings: list[str] = []
        pos_grunt_kg = Decimal("0")
        pos_kraska_kg = Decimal("0")
        pos_finish_kg = Decimal("0")
        pos_cost = Decimal("0")

        if grunt:
            g_rate = _to_dec(grunt.consumption_rate) or Decimal("0")
            g_price = _to_dec(grunt.price_per_kg) or Decimal("0")
            pos_grunt_kg = area * g_rate * qty
            pos_cost += pos_grunt_kg * g_price
            verification_warnings.extend(verify_consumption_rate(grunt, ptm))

        if kraska:
            k_rate = _to_dec(kraska.consumption_rate) or Decimal("0")
            k_price = _to_dec(kraska.price_per_kg) or Decimal("0")
            pos_kraska_kg = area * ptm * k_rate * qty
            pos_cost += pos_kraska_kg * k_price
            verification_warnings.extend(verify_consumption_rate(kraska, ptm))

        if finish:
            f_rate = _to_dec(finish.consumption_rate) or Decimal("0")
            f_price = _to_dec(finish.price_per_kg) or Decimal("0")
            pos_finish_kg = area * f_rate * qty
            pos_cost += pos_finish_kg * f_price
            verification_warnings.extend(verify_consumption_rate(finish, ptm))

        if not grunt and not kraska and not finish:
            errors.append(
                f"Позиция '{item.get('mark', '?')}': "
                f"не найден подходящий состав для PTM={float(ptm)} мм, "
                f"REI={rei_minutes}, среда={environment}"
            )

        position = PositionCalculation(
            mark=item.get("mark"),
            type_name=item.get("type_name"),
            quantity=qty,
            unit_weight_kg=float(weight),
            unit_area_m2=float(area),
            reduced_thickness_mm=float(ptm),
            matched_composition_name=kraska.name if kraska else None,
            grunt_consumption_kg=float(pos_grunt_kg.quantize(Decimal("0.01"))),
            kraska_consumption_kg=float(pos_kraska_kg.quantize(Decimal("0.01"))),
            finish_consumption_kg=float(pos_finish_kg.quantize(Decimal("0.01"))),
            position_cost_rub=float(pos_cost.quantize(Decimal("0.01"))),
            verification_warnings=verification_warnings,
        )
        positions.append(position)

        total_area += area * qty
        total_weight += weight * qty
        total_quantity += qty
        grunt_total += pos_grunt_kg
        kraska_total += pos_kraska_kg
        finish_total += pos_finish_kg
        cost_total += pos_cost

        if not composition_info.get("grunt_name") and grunt:
            composition_info["grunt_name"] = grunt.name
            composition_info["grunt_rate_kgm2"] = float(_to_dec(grunt.consumption_rate) or 0)
            composition_info["grunt_price_per_kg"] = float(_to_dec(grunt.price_per_kg) or 0)
            composition_info["grunt_dry_residue"] = float(_to_dec(grunt.dry_residue) or 0) if grunt.dry_residue is not None else None
            composition_info["grunt_density"] = float(_to_dec(grunt.density) or 0) if grunt.density is not None else None
        if not composition_info.get("kraska_name") and kraska:
            composition_info["kraska_name"] = kraska.name
            composition_info["kraska_rate_kgm2mm"] = float(_to_dec(kraska.consumption_rate) or 0)
            composition_info["kraska_price_per_kg"] = float(_to_dec(kraska.price_per_kg) or 0)
            composition_info["kraska_dry_residue"] = float(_to_dec(kraska.dry_residue) or 0) if kraska.dry_residue is not None else None
            composition_info["kraska_density"] = float(_to_dec(kraska.density) or 0) if kraska.density is not None else None
        if not composition_info.get("finish_name") and finish:
            composition_info["finish_name"] = finish.name
            composition_info["finish_rate_kgm2"] = float(_to_dec(finish.consumption_rate) or 0)
            composition_info["finish_price_per_kg"] = float(_to_dec(finish.price_per_kg) or 0)
            composition_info["finish_dry_residue"] = float(_to_dec(finish.dry_residue) or 0) if finish.dry_residue is not None else None
            composition_info["finish_density"] = float(_to_dec(finish.density) or 0) if finish.density is not None else None

    totals = {
        "total_quantity": total_quantity,
        "total_weight_kg": float(total_weight.quantize(Decimal("0.01"))),
        "total_area_m2": float(total_area.quantize(Decimal("0.0001"))),
        "grunt_consumption_kg": float(grunt_total.quantize(Decimal("0.01"))),
        "kraska_consumption_kg": float(kraska_total.quantize(Decimal("0.01"))),
        "finish_consumption_kg": float(finish_total.quantize(Decimal("0.01"))),
        "total_material_cost_rub": float(cost_total.quantize(Decimal("0.01"))),
    }

    return FullCalculation(
        positions=positions,
        totals=totals,
        composition=composition_info,
        errors=errors,
    )
