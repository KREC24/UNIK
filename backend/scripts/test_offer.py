import sys, asyncio
sys.path.insert(0, 'K:/Projects/UNIK/backend')
from app.services.offer_service import generate_offer_pdf

# Test with empty items
pdf = generate_offer_pdf(
    object_name="РУСАЛ Красноярский алюминиевый завод. г. Красноярск, ул. Пограничников, 40",
    items=[
        {
            "name": "Покрытие металлоконструкций огнезащитными\nсоставами R-90 Arbecoat XT (толщина слоя 2,5 мм)",
            "quantity": "3 796,92",
            "unit": "м2",
            "price_per_unit": "1 750,00 ₽",
            "cost_without_vat": "6 644 610,00 ₽",
            "vat_amount": "1 461 814,20 ₽",
            "cost_with_vat": "8 106 424,20 ₽",
        },
    ],
)
with open('K:/Projects/UNIK/output/test_kp2.pdf', 'wb') as f:
    f.write(pdf)
print(f"Generated: {len(pdf)} bytes")
