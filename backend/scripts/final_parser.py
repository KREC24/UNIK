import sys
from pathlib import Path
import xlsxwriter

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.kmd_parser import KmdShippingParser

ROOT = Path(__file__).parent.parent.parent
TESTDOC = ROOT / "testdoc"
OUT = ROOT / "testxl" / "Ведомость_отправочных_марок.xlsx"

l2 = [f for f in TESTDOC.iterdir() if "л.2" in f.name and f.suffix == ".pdf"][0]
p = KmdShippingParser(l2)
r = p.parse()

items = []
for item in r.items:
    qty = int(float(item["quantity"])) if item.get("quantity") else 1
    items.append({
        "mark": item.get("mark"),
        "type_name": item.get("type_name"),
        "quantity": qty,
        "length_x": int(float(item["length_x"])) if item.get("length_x") else None,
        "width_y": int(float(item["width_y"])) if item.get("width_y") else None,
        "height_z": int(float(item["height_z"])) if item.get("height_z") else None,
        "unit_weight_kg": float(item["unit_weight_kg"]) if item.get("unit_weight_kg") else None,
        "total_weight_kg": float(item["total_weight_kg"]) if item.get("total_weight_kg") else None,
        "unit_area_m2": float(item["unit_area_m2"]) if item.get("unit_area_m2") else None,
        "total_area_m2": float(item["total_area_m2"]) if item.get("total_area_m2") else None,
    })

mass_total = sum(i["total_weight_kg"] or 0 for i in items)
area_total = sum(i["total_area_m2"] or 0 for i in items)

N = 15  # columns A-O

wb = xlsxwriter.Workbook(str(OUT), {"strings_to_numbers": False})
ws = wb.add_worksheet("Ведомость отправочных марок")

bd = 1
cf = "Calibri"

def fmt(**kw):
    return wb.add_format({"font_name": cf, "border": bd, **kw})

title_f  = fmt(font_size=14, bold=True, align="center", valign="vcenter")
meta_l   = fmt(font_size=10, bold=True, align="left", valign="vcenter")
meta_v   = fmt(font_size=10, align="left", valign="vcenter")
empty_f  = fmt(font_size=10, align="center", valign="vcenter")
ghdr     = fmt(font_size=10, bold=True, align="center", valign="vcenter", bg_color="#D9D9D9", text_wrap=True)
gsub     = fmt(font_size=9, bold=True, align="center", valign="vcenter", bg_color="#D9D9D9")
data_c   = fmt(font_size=10, align="center", valign="vcenter")
data_n   = fmt(font_size=10, align="center", valign="vcenter", num_format="0.0")
data_a   = fmt(font_size=10, align="center", valign="vcenter", num_format="0.00")
tot_l    = fmt(font_size=10, bold=True, align="left", valign="vcenter", bg_color="#D9D9D9")
tot_n    = fmt(font_size=10, bold=True, align="center", valign="vcenter", bg_color="#D9D9D9", num_format="0.0")
tot_a    = fmt(font_size=10, bold=True, align="center", valign="vcenter", bg_color="#D9D9D9", num_format="0.00")
tot_e    = fmt(font_size=10, bold=True, align="center", valign="vcenter", bg_color="#D9D9D9")

# ── Метаданные R0-R6 ──
ws.merge_range(0, 0, 0, N - 1, "Листов в разделе", title_f)

ws.write(1, 1, "Номер проекта", meta_l)
ws.merge_range(1, 5, 1, N - 1, "В068522/1540Д-416-55500-01-5.2-КМД", meta_v)

ws.write(2, 1, "Название проекта", meta_l)
ws.merge_range(2, 5, 2, N - 1, "Корпус сборочно-испытательного производства", meta_v)

ws.write(3, 1, "Дата", meta_l)
ws.merge_range(3, 5, 3, N - 1, "18.04.2025  16:07:41", meta_v)

ws.write(4, 1, "Составил", meta_l)
ws.merge_range(4, 5, 4, N - 1, "", meta_v)

for c in range(N):
    ws.write(5, c, "", empty_f)

ws.merge_range(6, 0, 6, N - 1, "Ведомость отправочных марок", title_f)

# ── R7: шапка ──
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

# ── R8: подзаголовки ──
sub = ["", "", "", "", "", "По X", "По Y", "По Z", "Одной", "Всех", "Одной", "Всех", "", "", ""]
for c, s in enumerate(sub):
    ws.write(8, c, s, gsub)

# ── Данные R9+ ──
DR = 9
for i, item in enumerate(items):
    r = DR + i
    ws.write(r, 0, i + 1, data_c)
    ws.write(r, 1, item["mark"] or "", data_c)
    ws.write(r, 2, "", data_c)
    ws.write(r, 3, item["type_name"] or "", data_c)
    ws.write(r, 4, item["quantity"], data_c)
    ws.write(r, 5, item["length_x"], data_c)
    ws.write(r, 6, item["width_y"], data_c)
    ws.write(r, 7, item["height_z"], data_c)
    ws.write(r, 8, item["unit_weight_kg"], data_n)
    ws.write(r, 9, item["total_weight_kg"], data_n)
    ws.write(r, 10, item["unit_area_m2"], data_a)
    ws.write(r, 11, item["total_area_m2"], data_a)
    ws.write(r, 12, "", data_c)
    ws.write(r, 13, "", data_c)
    ws.write(r, 14, "", data_c)

# ── Итого ──
TR = DR + len(items)
for c in range(N):
    ws.write(TR, c, "", tot_e)
ws.write(TR, 0, "ИТОГО:", tot_l)
ws.write(TR, 9, round(mass_total, 1), tot_n)
ws.write(TR, 11, round(area_total, 2), tot_a)

# ── Ширина ──
ws.set_column(0, 0, 7)
ws.set_column(1, 1, 14)
ws.set_column(2, 2, 3)
ws.set_column(3, 3, 22)
ws.set_column(4, 4, 8)
ws.set_column(5, 5, 8)
ws.set_column(6, 6, 8)
ws.set_column(7, 7, 8)
ws.set_column(8, 8, 10)
ws.set_column(9, 9, 13)
ws.set_column(10, 10, 10)
ws.set_column(11, 11, 12)
ws.set_column(12, 12, 8)
ws.set_column(13, 13, 8)
ws.set_column(14, 14, 8)

ws.set_row(0, 22)
ws.set_row(6, 22)
ws.set_row(7, 30)
ws.set_row(8, 18)

ws.autofilter(DR - 1, 0, TR, N - 1)
ws.freeze_panes(DR, 2)

wb.close()

assert abs(round(mass_total, 1) - 263812.6) < 0.5, f"Mass {mass_total} != 263812.6"
