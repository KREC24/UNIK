"""Quick test of OGZ calculator core functions."""
import sys
sys.path.insert(0, "backend")

from decimal import Decimal
from app.core.ogz_calculator import (
    calculate_reduced_thickness,
    match_compositions,
    calculate_ogz_full,
    CompositionRecord,
)
from app.schemas.ogz import OgzCalculationRequest, OgzLineItemInput
from app.services.ogz_service import calculate_ogz

# Test 1: reduced thickness
thk = calculate_reduced_thickness(1000, 10)
print(f"Test 1 - Reduced thickness (1000 kg, 10 m2): {thk} mm")
assert 12.0 < float(thk) < 13.5, f"Expected ~12.74, got {thk}"

# Test 2: composition matching by PTM
default_compositions = [
    CompositionRecord(
        name="Грунт ГФ-021", composition_type="grunt",
        consumption_rate=Decimal("0.30"), price_per_kg=Decimal("500"),
        dry_residue=Decimal("65"), density=Decimal("1.5"),
        min_ptm_mm=Decimal("0"), max_ptm_mm=Decimal("30"),
        rei_minutes=90, environment="влажная",
    ),
    CompositionRecord(
        name="Краска Термобарьер", composition_type="kraska",
        consumption_rate=Decimal("0.90"), price_per_kg=Decimal("1200"),
        dry_residue=Decimal("70"), density=Decimal("1.2"),
        min_ptm_mm=Decimal("0"), max_ptm_mm=Decimal("30"),
        rei_minutes=90, environment="влажная",
    ),
    CompositionRecord(
        name="Финиш ПФ-115", composition_type="finish",
        consumption_rate=Decimal("0.25"), price_per_kg=Decimal("400"),
        dry_residue=Decimal("55"), density=Decimal("1.1"),
        min_ptm_mm=Decimal("0"), max_ptm_mm=Decimal("30"),
        rei_minutes=90, environment="влажная",
    ),
]

matched = match_compositions(default_compositions, thk, 90, "влажная")
print(f"Test 2 - Matched {len(matched)} compositions:")
for ctype, comp in matched.items():
    print(f"  {ctype}: {comp.name} rate={comp.consumption_rate} price={comp.price_per_kg}")

# Test 3: full calculation
items = [
    {"mark": "K1", "type_name": "Балка", "quantity": 5, "total_weight_kg": Decimal("1000"), "total_area_m2": Decimal("10")},
    {"mark": "K2", "type_name": "Колонна", "quantity": 3, "total_weight_kg": Decimal("800"), "total_area_m2": Decimal("8")},
]
result = calculate_ogz_full(items, default_compositions, 90, "влажная")
print(f"\nTest 3 - Full calculation:")
print(f"  Positions: {len(result.positions)}")
for p in result.positions:
    print(f"    {p.mark}: qty={p.quantity} wt={p.unit_weight_kg} area={p.unit_area_m2} thk={p.reduced_thickness_mm} grunt={p.grunt_consumption_kg} kraska={p.kraska_consumption_kg}")
print(f"  Totals: area={result.totals['total_area_m2']} grunt={result.totals['grunt_consumption_kg']} kraska={result.totals['kraska_consumption_kg']} cost={result.totals['total_material_cost_rub']}")

# Test 4: full service with OgzCalculationRequest
req = OgzCalculationRequest(
    items=[
        OgzLineItemInput(mark="K1", type_name="Балка", quantity=Decimal("5"), total_weight_kg=Decimal("1000"), total_area_m2=Decimal("10")),
        OgzLineItemInput(mark="K2", type_name="Колонна", quantity=Decimal("3"), total_weight_kg=Decimal("800"), total_area_m2=Decimal("8")),
    ],
    rei=90,
    environment="влажная",
)
# Convert compositions to dicts for service layer
compositions_as_dicts = [
    {
        "name": c.name, "composition_type": c.composition_type,
        "consumption_rate": c.consumption_rate, "price_per_kg": c.price_per_kg,
        "dry_residue": c.dry_residue, "density": c.density,
        "min_ptm_mm": c.min_ptm_mm, "max_ptm_mm": c.max_ptm_mm,
        "rei_minutes": c.rei_minutes, "environment": c.environment,
    }
    for c in default_compositions
]
response = calculate_ogz(req, compositions=compositions_as_dicts)
print(f"\nTest 4 - Full service call:")
print(f"  Positions: {len(response.positions)}")
for p in response.positions:
    print(f"    {p.mark}: qty={p.quantity} thk={p.reduced_thickness_mm} grunt={p.grunt_consumption_kg} kraska={p.kraska_consumption_kg} cost={p.position_cost_rub}")
print(f"  Totals: area={response.totals.total_area_m2} grunt={response.totals.grunt_consumption_kg} kraska={response.totals.kraska_consumption_kg} cost={response.totals.total_material_cost_rub}")
if response.composition:
    print(f"  Composition: REI={response.composition.rei_minutes} env={response.composition.environment}")

print("\n=== ALL TESTS PASSED ===")
