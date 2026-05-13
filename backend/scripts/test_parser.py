"""
Тестовый запуск парсера на данных testdoc и сверка с эталоном testxl.

Использование:
    python -m backend.scripts.test_parser
    или
    python backend/scripts/test_parser.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.parsing_service import parse_shipping_list, parse_general_data, parse_revC04

TESTDOC = project_root / "testdoc"
TESTXL = project_root / "testxl"
OUTPUT_DIR = project_root / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def find_file(pattern: str, directory: Path) -> Path | None:
    for f in directory.iterdir():
        if f.is_file() and pattern.lower() in f.name.lower():
            return f
    return None


def test_shipping_parser():
    pdf_path = find_file("л.2", TESTDOC) or find_file("ведомость", TESTDOC)
    if not pdf_path:
        print("[ERROR] Не найден PDF с ведомостью отправочных марок (л.2)")
        return None

    print(f"[TEST] Парсинг: {pdf_path.name}")
    result = parse_shipping_list(pdf_path)

    print(f"  Распознано строк: {result.total_rows_parsed} / {result.total_rows_raw}")
    print(f"  Успешность: {result.success_rate:.1%}")
    print(f"  Нераспознано: {len(result.unrecognized_rows)}")
    print(f"  Ошибок: {len(result.errors)}")
    if result.errors:
        for e in result.errors:
            print(f"    - {e[:200]}")

    if result.metadata.project_code:
        print(f"  Проект: {result.metadata.project_code}")

    print("\n  Первые 10 строк:")
    for item in result.items[:10]:
        print(
            f"    #{item.position or '-'} | {item.mark or '-'} | "
            f"{item.type_name or '-'} | qty={item.quantity} | "
            f"dim={item.length_x}x{item.width_y}x{item.height_z} | "
            f"wt={item.total_weight_kg}kg | S={item.total_area_m2}m2"
        )

    print("\n  Последние 5 строк:")
    for item in result.items[-5:]:
        print(
            f"    #{item.position or '-'} | {item.mark or '-'} | "
            f"{item.type_name or '-'} | qty={item.quantity} | "
            f"wt={item.total_weight_kg}kg | S={item.total_area_m2}m2"
        )

    totals = {"total_weight": 0.0, "total_area": 0.0, "count": 0}
    for item in result.items:
        if item.total_weight_kg:
            totals["total_weight"] += float(item.total_weight_kg)
        if item.total_area_m2:
            totals["total_area"] += float(item.total_area_m2)
        totals["count"] += 1

    print(f"\n  ИТОГО: {totals['count']} позиций, "
          f"Масса={totals['total_weight']:.1f} кг, "
          f"Площадь={totals['total_area']:.2f} м2")

    if result.unrecognized_rows:
        print(f"\n  Нераспознанные строки (первые 10):")
        for row in result.unrecognized_rows[:10]:
            print(f"    {row.issues}: {str(row.partial_data)[:200]}")

    return result


def test_general_data_parser():
    pdf_path = find_file("л.1", TESTDOC) or find_file("общие", TESTDOC)
    if not pdf_path:
        print("[WARN] Не найден PDF с общими данными (л.1)")
        return None

    print(f"\n[TEST] Парсинг общих данных: {pdf_path.name}")
    result = parse_general_data(pdf_path)

    print(f"  Распознано профилей: {result.total_rows_parsed}")
    print(f"  Метаданные: {result.metadata.model_dump()}")

    for item in result.items[:15]:
        d = item.model_dump()
        print(
            f"    {d.get('profile_name', '-') or '-'} | "
            f"ГОСТ={d.get('gost_code', '-') or '-'} | "
            f"сталь={d.get('steel_grade', '-') or '-'} | "
            f"масса={d.get('unit_weight_kg', '-') or '-'} кг/м | "
            f"тип={d.get('section_type', '-') or '-'}"
        )

    return result


def test_revC04_parser():
    pdf_path = find_file("revC04", TESTDOC) or find_file("rev", TESTDOC)
    if not pdf_path:
        print("[WARN] Не найден PDF revC04")
        return None

    print(f"\n[TEST] Парсинг revC04: {pdf_path.name}")
    result = parse_revC04(pdf_path)

    print(f"  Распознано строк: {result.total_rows_parsed} / {result.total_rows_raw}")
    print(f"  Успешность: {result.success_rate:.1%}")
    print(f"  Нераспознано: {len(result.unrecognized_rows)}")
    print(f"  Ошибок: {len(result.errors)}")
    if result.errors:
        for e in result.errors:
            print(f"    - {e[:200]}")

    if result.metadata.project_code:
        print(f"  Проект: {result.metadata.project_code}")
    if result.metadata.object_name:
        print(f"  Объект: {result.metadata.object_name}")

    revs = result.metadata.model_dump().get("revisions", [])
    if revs:
        print(f"  Ревизий: {len(revs)}")

    print("\n  Первые 25 строк:")
    for item in result.items[:25]:
        d = item.model_dump()
        print(
            f"    #{d.get('position') or '-'} | {d.get('mark') or '-'} | "
            f"{d.get('profile_type') or '-'} | steel={d.get('steel_grade') or '-'} | "
            f"profile={d.get('ogz_notes') or '-'} | GOST={d.get('gost_code') or '-'}"
        )

    print("\n  Последние 10 строк:")
    for item in result.items[-10:]:
        d = item.model_dump()
        print(
            f"    #{d.get('position') or '-'} | {d.get('mark') or '-'} | "
            f"{d.get('profile_type') or '-'} | steel={d.get('steel_grade') or '-'} | "
            f"profile={d.get('ogz_notes') or '-'}"
        )

    profiles_by_type = {}
    for item in result.items:
        pt = item.profile_type or "прочее"
        profiles_by_type[pt] = profiles_by_type.get(pt, 0) + 1

    print(f"\n  Распределение по типам профилей:")
    for pt, count in sorted(profiles_by_type.items()):
        print(f"    {pt}: {count}")

    return result


def compare_with_reference(shipping_result):
    import pandas as pd

    xls_path = find_file("Shiping_list", TESTXL) or find_file(".xls", TESTXL)
    if not xls_path:
        print("[WARN] Не найден эталонный Excel")
        return

    print(f"\n[COMPARE] Сравнение с эталоном: {xls_path.name}")
    df = pd.read_excel(xls_path, header=None, engine="xlrd")

    total_rows_xls = len(df)
    non_null_rows = sum(
        1 for _, row in df.iterrows()
        if any(pd.notna(v) and str(v).strip() != "" for v in row)
    )
    print(f"  Строк в Excel: {total_rows_xls} (данных: {non_null_rows})")
    print(f"  Распознано парсером: {shipping_result.total_rows_parsed}")

    if shipping_result.total_rows_parsed >= non_null_rows * 0.7:
        print(f"  [OK] Парсер извлёк >=70% данных эталона")
    else:
        print(f"  [WARN] Парсер извлёк только "
              f"{shipping_result.total_rows_parsed}/{non_null_rows} строк "
              f"({shipping_result.total_rows_parsed/non_null_rows*100:.1f}%)")


def export_results(result, prefix="shipping"):
    if not result:
        return
    from app.services.export_service import export_json, export_csv, export_xlsx

    json_path = OUTPUT_DIR / f"{prefix}_result.json"
    csv_path = OUTPUT_DIR / f"{prefix}_result.csv"
    xlsx_path = OUTPUT_DIR / f"{prefix}_result.xlsx"

    import json
    json_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\n[EXPORT] JSON -> {json_path}")
    print(f"[EXPORT] Результаты также доступны через API: /api/v1/parse/batches/{{id}}/export/json|csv|xlsx")


if __name__ == "__main__":
    print("=" * 70)
    print("UNIK Parser Engine — Тестовый запуск")
    print("=" * 70)

    shipping = test_shipping_parser()
    general = test_general_data_parser()
    revc04 = test_revC04_parser()

    if shipping:
        compare_with_reference(shipping)
        export_results(shipping, "shipping")
    if general:
        export_results(general, "general")
    if revc04:
        export_results(revc04, "revC04")

    print("\n" + "=" * 70)
    print("Тестирование завершено.")
    print("=" * 70)
