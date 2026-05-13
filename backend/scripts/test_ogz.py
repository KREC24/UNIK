"""Quick test of OGZ calculator core functions."""
import sys
sys.path.insert(0, "backend")

from decimal import Decimal
from app.core.ogz_calculator import (
    calculate_reduced_thickness,
    select_ogz_composition,
    calculate_material_consumption,
)
from app.schemas.ogz import OgzCalculationRequest, OgzLineItemInput
from app.services.ogz_service import calculate_ogz

# Test 1: reduced thickness
thk = calculate_reduced_thickness(1000, 10)
print(f"Test 1 - Reduced thickness (1000 kg, 10 m2): {thk} mm")
assert 12.0 < float(thk) < 13.5, f"Expected ~12.74, got {thk}"

# Test 2: composition selection
comp = select_ogz_composition(90, thk, "влажная")
print(f"Test 2 - Composition REI={comp.rei_minutes}, env={comp.environment}")
print(f"  Grunt: {comp.grunt.name} rate={comp.grunt.consumption_rate} price={comp.grunt.price_per_kg}")
print(f"  Kraska: {comp.kraska.name} rate={comp.kraska.consumption_rate} price={comp.kraska.price_per_kg}")
print(f"  Finish: {comp.finish.name} rate={comp.finish.consumption_rate} price={comp.finish.price_per_kg}")

# Test 3: material consumption (raw dicts)
items = [
    {"mark": "K1", "type_name": "Балка", "quantity": 5, "total_weight_kg": Decimal("1000"), "total_area_m2": Decimal("10")},
    {"mark": "K2", "type_name": "Колонна", "quantity": 3, "total_weight_kg": Decimal("800"), "total_area_m2": Decimal("8")},
]
result = calculate_material_consumption(items, comp)
print(f"\nTest 3 - Material consumption:")
print(f"  Positions: {len(result['positions'])}")
for p in result["positions"]:
    print(f"    {p['mark']}: qty={p['quantity']} wt={p['unit_weight_kg']} area={p['unit_area_m2']} thk={p['reduced_thickness_mm']} grunt={p['grunt_consumption_kg']} kraska={p['kraska_consumption_kg']}")
totals = result["totals"]
print(f"  Totals: area={totals['total_area_m2']} grunt={totals['grunt_consumption_kg']} kraska={totals['kraska_consumption_kg']} cost={totals['total_material_cost_rub']}")

# Test 4: full service with OgzCalculationRequest
req = OgzCalculationRequest(
    items=[
        OgzLineItemInput(mark="K1", type_name="Балка", quantity=Decimal("5"), total_weight_kg=Decimal("1000"), total_area_m2=Decimal("10")),
        OgzLineItemInput(mark="K2", type_name="Колонна", quantity=Decimal("3"), total_weight_kg=Decimal("800"), total_area_m2=Decimal("8")),
    ],
    rei=90,
    environment="влажная",
)
response = calculate_ogz(req)
print(f"\nTest 4 - Full service call:")
print(f"  Positions: {len(response.positions)}")
for p in response.positions:
    print(f"    {p.mark}: qty={p.quantity} thk={p.reduced_thickness_mm} grunt={p.grunt_consumption_kg} kraska={p.kraska_consumption_kg} cost={p.position_cost_rub}")
print(f"  Totals: area={response.totals.total_area_m2} grunt={response.totals.grunt_consumption_kg} kraska={response.totals.kraska_consumption_kg} cost={response.totals.total_material_cost_rub}")
if response.composition:
    print(f"  Composition: REI={response.composition.rei_minutes} env={response.composition.environment}")

print("\n=== ALL TESTS PASSED ===")
