"""
Заполнение справочника OgzComposition типовыми составами ОГЗ.

Запуск: python backend/scripts/seed_ogz.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from decimal import Decimal

SEED_DATA = [
    {
        "name": "Грунт ГФ-021",
        "composition_type": "grunt",
        "consumption_rate": Decimal("0.30"),
        "price_per_kg": Decimal("500.00"),
        "dry_residue": Decimal("65"),
        "density": Decimal("1.5"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("30"),
        "rei_minutes": None,
        "environment": None,
    },
    {
        "name": "Грунт ГФ-021 (агрессивная среда)",
        "composition_type": "grunt",
        "consumption_rate": Decimal("0.40"),
        "price_per_kg": Decimal("550.00"),
        "dry_residue": Decimal("65"),
        "density": Decimal("1.5"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("30"),
        "rei_minutes": None,
        "environment": "агрессивная",
    },
    {
        "name": "Краска Термобарьер",
        "composition_type": "kraska",
        "consumption_rate": Decimal("0.90"),
        "price_per_kg": Decimal("1200.00"),
        "dry_residue": Decimal("70"),
        "density": Decimal("1.2"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("20"),
        "rei_minutes": 90,
        "environment": None,
    },
    {
        "name": "Краска Термобарьер-2 (REI 120)",
        "composition_type": "kraska",
        "consumption_rate": Decimal("1.10"),
        "price_per_kg": Decimal("1350.00"),
        "dry_residue": Decimal("70"),
        "density": Decimal("1.2"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("20"),
        "rei_minutes": 120,
        "environment": None,
    },
    {
        "name": "Финиш ПФ-115",
        "composition_type": "finish",
        "consumption_rate": Decimal("0.25"),
        "price_per_kg": Decimal("400.00"),
        "dry_residue": Decimal("55"),
        "density": Decimal("1.1"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("30"),
        "rei_minutes": None,
        "environment": None,
    },
    {
        "name": "Финиш ХВ-785",
        "composition_type": "finish",
        "consumption_rate": Decimal("0.30"),
        "price_per_kg": Decimal("450.00"),
        "dry_residue": Decimal("50"),
        "density": Decimal("1.0"),
        "min_ptm_mm": Decimal("0"),
        "max_ptm_mm": Decimal("30"),
        "rei_minutes": None,
        "environment": None,
    },
]


def seed_in_memory():
    """Вывод seed-данных для использования в API."""
    print("=" * 60)
    print("  SEED DATA: OGZ compositions")
    print("=" * 60)
    for i, comp in enumerate(SEED_DATA, 1):
        suffix = "/mm" if comp['composition_type'] == 'kraska' else ""
        print(f"\n{i}. {comp['name']}")
        print(f"   Type:         {comp['composition_type']}")
        print(f"   Rate:         {comp['consumption_rate']} kg/m2{suffix}")
        print(f"   Price:        {comp['price_per_kg']} RUB/kg")
        print(f"   Dry residue:  {comp['dry_residue']}%")
        print(f"   Density:      {comp['density']} g/cm3")
        print(f"   PTM range:    {comp['min_ptm_mm']}–{comp['max_ptm_mm']} mm")
        if comp['rei_minutes']:
            print(f"   REI:          {comp['rei_minutes']} min")
        if comp['environment']:
            print(f"   Environment:  {comp['environment']}")

    print("\n" + "=" * 60)
    print("  Summary:")
    print("  Grunt GF-021:       0.30 kg/m²    x 500 RUB/kg   (65%, 1.5 g/cm³)")
    print("  Kraska Termobarrier: 0.90 kg/m²/mm x 1200 RUB/kg  (70%, 1.2 g/cm³)")
    print("  Finish PF-115:      0.25 kg/m²    x 400 RUB/kg   (55%, 1.1 g/cm³)")
    print("=" * 60)


def seed_database():
    """Запись seed-данных в БД (PostgreSQL)."""
    try:
        import asyncio
        from app.models.database import OgzComposition
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.config import settings

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async def _seed():
            async with session_factory() as session:
                for comp_data in SEED_DATA:
                    comp = OgzComposition(**comp_data)
                    session.add(comp)
                await session.commit()
                print(f"Inserted {len(SEED_DATA)} compositions into ogz_compositions")

        asyncio.run(_seed())
    except ImportError as e:
        print(f"DB connection failed: {e}")
        print("Use seed_in_memory() for data output.")


if __name__ == "__main__":
    if "--db" in sys.argv:
        seed_database()
    else:
        seed_in_memory()
        print("\nFor DB insert: python backend/scripts/seed_ogz.py --db")
