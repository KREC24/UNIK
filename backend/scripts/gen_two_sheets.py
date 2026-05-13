"""
Генерирует две ведомости отправочных марок из testdoc1:
- Ведомость_отправочных_марок_R45.xlsx
- Ведомость_отправочных_марок_R60.xlsx

Формат — точная копия эталона Shiping_list_выбр_18.04.25 по 5.2 ведомость.xls,
15 колонок A-O, метаданные R0-R6, шапка R7-R8, данные R9+.
"""
import re
import sys
from datetime import datetime
from pathlib import Path
import pdfplumber
import xlsxwriter

PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTDOC1_DIR = (
    PROJECT_ROOT / "testdoc1_extracted"
    / "Многофункциональный физкультурно-оздоровительный комплекс по адаптивным видам спорта в г. Красноярске"
)
TESTXL1 = PROJECT_ROOT / "testxl1"
TESTXL1.mkdir(parents=True, exist_ok=True)

PROJECT_META = {
    "project_code": "149-24-ПБ изм.3",
    "project_name": "Многофункциональный физкультурно-оздоровительный комплекс по адаптивным видам спорта",
    "project_address": "г. Красноярск, пер. Афонтовский, 7",
    "stage": "П",
    "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
}

# Профили из КМ (эталонные данные для сверки)
KM_BEAMS = {
    "I 20Ш2": [
        {"mark": "Пр1", "descr": "Прогон Пр1 / Балка 20Ш2, L=6000, С345", "qty": 60, "unit_kg": 232.80},
        {"mark": "Пр2", "descr": "Прогон Пр2 / Балка 20Ш2, L=7500, С345", "qty": 24, "unit_kg": 291.00},
    ],
}

# Очистка названий профилей
def clean_mark(raw: str) -> str:
    for old, new in [
        ("☐", "Труба "), ("\u2610", "Труба "),
        ("I ", "Балка "), ("Ø", "Круг "), ("ø", "Круг "),
        ("L", "Уголок "), ("[", "Швеллер "),
    ]:
        raw = raw.replace(old, new)
    raw = re.sub(r"([а-яё]+)\s+\1", r"\1", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s{2,}", " ", raw)
    return raw.strip()


def find_pdf(keyword: str) -> Path | None:
    for f in sorted(TESTDOC1_DIR.iterdir()):
        if f.suffix.lower() == ".pdf" and keyword.lower() in f.name.lower():
            return f
    return None


def extract_items(pdf_path: Path, target_r: int) -> list[dict]:
    """Извлекает строки из PDF расчёта ОГЗ. target_r: 45 или 60."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join((page.extract_text() or "") for page in pdf.pages)

    lines = full_text.split("\n")
    current_section = ""

    data_pat = re.compile(
        r"^(.+?)\s+(\d+,\d+)\s+(\d+,\d+)\s+(\S.*?\S)\s+R(\d+)\s+(\d+,\d+)"
    )

    section_keywords = [
        "Надколонн", "Связи по", "Связ", "Ферм", "Балк", "Прогон",
        "Колонн", "Стойк", "Распорк", "Ригел", "Обвяз", "Лестниц",
    ]

    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        for kw in sorted(section_keywords, key=len, reverse=True):
            if line.startswith(kw):
                remaining = line[len(kw):].strip()
                m2 = re.match(r"^([а-яё]+\s+)?(.*)", remaining, re.IGNORECASE)
                if m2:
                    remaining = m2.group(2) or remaining
                if len(remaining) > 3:
                    current_section = kw.rstrip("и").strip()
                    line = remaining
                break

        m = data_pat.match(line)
        if not m:
            continue

        profile_raw = m.group(1).strip()
        mass_ton = float(m.group(2).replace(",", "."))
        area_m2 = float(m.group(3).replace(",", "."))
        coating = m.group(4).strip()
        r_value = int(m.group(5))
        ptm_mm = float(m.group(6).replace(",", "."))

        # Классификация типа элемента
        type_name = _classify(profile_raw, current_section)

        items.append({
            "mark_raw": profile_raw,
            "mark": clean_mark(profile_raw),
            "type_name": type_name,
            "quantity": None,
            "length_x": None,
            "width_y": None,
            "height_z": None,
            "unit_weight_kg": None,
            "total_weight_kg": round(mass_ton * 1000, 1),
            "unit_area_m2": None,
            "total_area_m2": round(area_m2, 2),
            "ptm": round(ptm_mm, 2),
            "r_value": r_value,
            "coating": coating,
            "steel_grade": None,
        })

    return items


def _classify(profile: str, section: str) -> str:
    sl = section.lower()
    if "надколон" in sl: return "Надколонник"
    if "связ" in sl: return "Связь"
    if "ферм" in sl: return "Ферма"
    if "балк" in sl: return "Балка"
    if "прогон" in sl: return "Прогон"
    if "колон" in sl: return "Колонна"
    if "стойк" in sl: return "Стойка"
    if "распор" in sl: return "Распорка"
    if "ригел" in sl: return "Ригель"
    if "обвяз" in sl: return "Обвязка"
    if "лестниц" in sl: return "Лестница"
    p = profile.upper().replace("\u2610", "").strip()
    if p.startswith("I") or p.startswith("БАЛКА"): return "Балка"
    if "ТРУБА" in p or "П" in p: return "Труба профильная"
    if p.startswith("L") or "УГОЛОК" in p: return "Уголок"
    if "КРУГ" in p or "Ø" in p or "ø" in p: return "Круг"
    return section if section else "Элемент"


def expand_items(items: list[dict], target_r: int) -> list[dict]:
    """
    Раскладывает агрегированные записи на поэлементные,
    используя данные из КМ (если доступны).
    """
    expanded = []
    for item in items:
        raw = item["mark_raw"]
        found = False
        for km_key, km_rows in KM_BEAMS.items():
            if km_key.lower() in raw.lower():
                agg_mass = float(item["total_weight_kg"] or 0)
                agg_area = float(item["total_area_m2"] or 0)
                for km in km_rows:
                    unit_kg = km["unit_kg"]
                    total_kg = round(unit_kg * km["qty"], 1) if unit_kg else None
                    total_area = round(agg_area * (total_kg / agg_mass), 2) if (total_kg and agg_mass) else None
                    unit_area = round(total_area / km["qty"], 2) if (total_area and km["qty"]) else None
                    expanded.append({
                        **{k: v for k, v in item.items() if k not in (
                            "total_weight_kg", "total_area_m2",
                            "unit_weight_kg", "unit_area_m2",
                            "quantity", "mark", "type_name",
                        )},
                        "mark": km["mark"],
                        "type_name": km["descr"],
                        "quantity": km["qty"],
                        "unit_weight_kg": unit_kg,
                        "total_weight_kg": total_kg,
                        "unit_area_m2": unit_area,
                        "total_area_m2": total_area,
                    })
                found = True
                break
        if not found:
            expanded.append({**item, "quantity": 1})
    return expanded


def write_xlsx(items: list[dict], out_path: Path, r_label: str):
    """Создаёт XLSX в формате эталона Shiping_list."""
    wb = xlsxwriter.Workbook(str(out_path), {"strings_to_numbers": False})
    ws = wb.add_worksheet("Ведомость отправочных марок")

    N = 15  # колонок A-O
    bd = 1
    cf = "Calibri"

    def fmt(**kw):
        return wb.add_format({"font_name": cf, "border": bd, **kw})

    # ── Метаданные R0-R5 ──
    title_f = fmt(font_size=14, bold=True, align="center", valign="vcenter")
    ws.merge_range(0, 0, 0, N - 1, "Листов в разделе", title_f)

    meta_l = fmt(font_size=10, bold=True, align="left", valign="vcenter")
    meta_v = fmt(font_size=10, align="left", valign="vcenter")
    ws.write(1, 1, "Номер проекта", meta_l)
    ws.merge_range(1, 5, 1, N - 1, PROJECT_META["project_code"], meta_v)
    ws.write(2, 1, "Название проекта", meta_l)
    ws.merge_range(2, 5, 2, N - 1, PROJECT_META["project_name"], meta_v)
    ws.write(3, 1, "Дата", meta_l)
    ws.merge_range(3, 5, 3, N - 1, PROJECT_META["date"], meta_v)
    ws.write(4, 1, "Составил", meta_l)
    ws.merge_range(4, 5, 4, N - 1, "", meta_v)

    empty_f = fmt(font_size=10, align="center", valign="vcenter")
    for c in range(N):
        ws.write(5, c, "", empty_f)

    ws.merge_range(6, 0, 6, N - 1,
        f"Ведомость отправочных марок — предел огнестойкости {r_label}",
        title_f)

    # ── R7: Шапка ──
    ghdr = fmt(font_size=10, bold=True, align="center", valign="vcenter",
               bg_color="#D9D9D9", text_wrap=True)
    gsub = fmt(font_size=9, bold=True, align="center", valign="vcenter",
               bg_color="#D9D9D9")

    ws.write(7, 0, "Лист №", ghdr)
    ws.write(7, 1, "Марка", ghdr)
    ws.write(7, 2, "", ghdr)
    ws.write(7, 3, "Описание", ghdr)
    ws.write(7, 4, "Кол-во", ghdr)
    ws.merge_range(7, 5, 7, 7, "Габарит, мм", ghdr)
    ws.merge_range(7, 8, 7, 9, "Масса, кг", ghdr)
    ws.merge_range(7, 10, 7, 11, "Площадь, м²", ghdr)
    ws.write(7, 12, "Прим.", ghdr)
    ws.write(7, 13, "ОГЗ", ghdr)
    ws.write(7, 14, "RAL", ghdr)

    # ── R8: Подзаголовки ──
    sub = ["", "", "", "", "", "По X", "По Y", "По Z",
           "Одной", "Всех", "Одной", "Всех", "", "", ""]
    for c, s in enumerate(sub):
        ws.write(8, c, s, gsub)

    # ── Данные R9+ ──
    data_c = fmt(font_size=10, align="center", valign="vcenter")
    data_n = fmt(font_size=10, align="center", valign="vcenter", num_format="0.0")
    data_a = fmt(font_size=10, align="center", valign="vcenter", num_format="0.00")

    DR = 9
    mass_total = 0.0
    area_total = 0.0

    for i, item in enumerate(items):
        r = DR + i
        tw = float(item["total_weight_kg"] or 0)
        ta = float(item["total_area_m2"] or 0)
        mass_total += tw
        area_total += ta

        ws.write(r, 0, i + 1, data_c)
        ws.write(r, 1, item["mark"], data_c)
        ws.write(r, 2, "", data_c)
        ws.write(r, 3, item["type_name"], data_c)
        ws.write(r, 4, item.get("quantity"), data_c)
        ws.write(r, 5, item.get("length_x"), data_c)
        ws.write(r, 6, item.get("width_y"), data_c)
        ws.write(r, 7, item.get("height_z"), data_c)
        ws.write(r, 8, item.get("unit_weight_kg"), data_n)
        ws.write(r, 9, tw, data_n)
        ws.write(r, 10, item.get("unit_area_m2"), data_a)
        ws.write(r, 11, ta, data_a)
        ws.write(r, 12, "", data_c)
        ws.write(r, 13, f"R{item['r_value']}", data_c)
        ws.write(r, 14, "", data_c)

    # ── Итого ──
    TR = DR + len(items)
    tot_e = fmt(font_size=11, bold=True, align="center", valign="vcenter",
                bg_color="#D9D9D9")
    tot_l = fmt(font_size=11, bold=True, align="left", valign="vcenter",
                bg_color="#D9D9D9")
    tot_n = fmt(font_size=11, bold=True, align="center", valign="vcenter",
                bg_color="#D9D9D9", num_format="0.0")
    tot_a = fmt(font_size=11, bold=True, align="center", valign="vcenter",
                bg_color="#D9D9D9", num_format="0.00")

    for c in range(N):
        ws.write(TR, c, "", tot_e)
    ws.write(TR, 0, "ИТОГО:", tot_l)
    ws.write(TR, 9, round(mass_total, 1), tot_n)
    ws.write(TR, 11, round(area_total, 2), tot_a)

    # ── Ширина колонок ──
    ws.set_column(0, 0, 7)    # Лист №
    ws.set_column(1, 1, 14)   # Марка
    ws.set_column(2, 2, 3)    # (empty)
    ws.set_column(3, 3, 22)   # Описание
    ws.set_column(4, 4, 8)    # Кол-во
    ws.set_column(5, 5, 8)    # X
    ws.set_column(6, 6, 8)    # Y
    ws.set_column(7, 7, 8)    # Z
    ws.set_column(8, 8, 10)   # Масса ед.
    ws.set_column(9, 9, 13)   # Масса общ.
    ws.set_column(10, 10, 10) # S ед.
    ws.set_column(11, 11, 12) # S общ.
    ws.set_column(12, 12, 8)  # Прим.
    ws.set_column(13, 13, 8)  # ОГЗ
    ws.set_column(14, 14, 8)  # RAL

    ws.set_row(0, 22)
    ws.set_row(6, 22)
    ws.set_row(7, 30)
    ws.set_row(8, 18)

    ws.autofilter(DR - 1, 0, TR, N - 1)
    ws.freeze_panes(DR, 2)

    wb.close()
    print(f"  Total mass: {mass_total:.1f} kg ({mass_total/1000:.2f} t)")
    print(f"  Total area: {area_total:.2f} m2")


def main():
    r45_pdf = find_pdf("R45")
    r60_pdf = find_pdf("R60")

    if not r45_pdf or not r60_pdf:
        print("ERROR: PDF files not found")
        sys.exit(1)

    print(f"R45 source: {r45_pdf.name}")
    print(f"R60 source: {r60_pdf.name}")

    for label, pdf_path, r_val, out_name in [
        ("R45", r45_pdf, 45, "Ведомость_отправочных_марок_R45.xlsx"),
        ("R60", r60_pdf, 60, "Ведомость_отправочных_марок_R60.xlsx"),
    ]:
        print(f"\n{'='*60}")
        print(f"  {label} — извлечение данных...")
        items = extract_items(pdf_path, r_val)
        print(f"  Профилей (агрегированно): {len(items)}")

        items = expand_items(items, r_val)
        items.sort(key=lambda x: float(x["total_weight_kg"] or 0), reverse=True)
        print(f"  Строк после разложения: {len(items)}")

        out_path = TESTXL1 / out_name
        write_xlsx(items, out_path, label)

    print(f"\n{'='*60}")
    print(f"Готово. Файлы в: {TESTXL1}")
    for f in sorted(TESTXL1.iterdir()):
        if f.suffix == ".xlsx":
            print(f"  {f.name}")


if __name__ == "__main__":
    main()
