"""
Генератор коммерческого предложения (КП) — точная копия реального КП ООО «НИК».

v2: PyMuPDF TextWriter для корректной поддержки кириллицы.
"""
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional
import logging

import fitz  # PyMuPDF

from app.config import settings

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
STAMP_PATH = ASSETS_DIR / "stamp.jpeg"
FONT_REGULAR_PATH = str(ASSETS_DIR / "arial.ttf")
FONT_BOLD_PATH = str(ASSETS_DIR / "arialbd.ttf")

VAT_RATE = Decimal("22")
VAT_FACTOR = Decimal("1.22")

COMPANY_DEFAULTS = {
    "name": "ООО «НИК»",
    "phone": "8 (391) 208-27-67",
    "email": "ognis.org@mail.ru",
    "license": "Лицензия МЧС № 24-Б/00921 от 28.12.2020г. Л014-00101-24/00132407",
    "accreditation": "Регистрационный номер акредитации: 24-17-2023-002629 (Номер ЕРУЛ: Т002-00101-24/01006338)",
    "guarantee_years": 5,
    "workers_count": "5-6",
    "payment_terms": (
        "авансовый платеж по договору 40% при подписании договора, "
        "30% после выполнения 50% объема работ, "
        "оплата оставшегося объема после сдачи в течении 20 календарных дней"
    ),
    "documents_package": (
        "Проект огнезащиты, сертификаты на применяемые материалы, "
        "заверенная копия лицензии мчс исполнителя, документы ПСА, таблица МК, "
        "протокол ИПЛ, АОСР, акты выполненных работ"
    ),
}

MARGIN_LEFT = 42
MARGIN_RIGHT = 28
MARGIN_TOP = 30
PAGE_WIDTH = 595
PAGE_HEIGHT = 842
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT


def _fmt_price(value: Decimal) -> str:
    s = f"{value:,.2f}"
    s = s.replace(",", " ").replace(".", ",").replace(" ", "X").replace(",", ".")
    whole, frac = s.split(".")
    whole = whole.replace("X", " ")
    return f"{whole},{frac} ₽"


def _fmt_num(value: Decimal, decimals: int = 2) -> str:
    s = f"{value:,.{decimals}f}"
    s = s.replace(",", " ").replace(".", ",").replace(" ", "X").replace(",", ".")
    if "." in s:
        whole, frac = s.split(".")
        whole = whole.replace("X", " ")
        return f"{whole},{frac}"
    return s.replace("X", " ")


def _tw_text(tw: fitz.TextWriter, point: tuple, text: str, font: fitz.Font, fontsize: float,
             color: tuple = (0, 0, 0)):
    """Append text to TextWriter with proper Unicode encoding."""
    tw.append(point, text, font=font, fontsize=fontsize)


def _tw_span(tw: fitz.TextWriter, rect: fitz.Rect, text: str, font: fitz.Font, fontsize: float,
             color: tuple = (0, 0, 0), align: int = fitz.TEXT_ALIGN_LEFT):
    """Write a text span with positioning."""
    tw.append(rect.tl, text, font=font, fontsize=fontsize)


def generate_offer_pdf(
    object_name: str,
    date_str: str | None = None,
    items: list[dict] | None = None,
    company: dict | None = None,
) -> bytes:
    if date_str is None:
        now = datetime.now(timezone.utc)
        months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        date_str = f"от «{now.day} » {months[now.month]} {now.year} г."

    cfg = {**COMPANY_DEFAULTS, **(company or {})}
    row_data = items or []

    col_widths = [22, 200, 50, 32, 52, 58, 52, 58]
    col_positions = [MARGIN_LEFT]
    for w in col_widths:
        col_positions.append(col_positions[-1] + w)

    doc = fitz.open()

    font_reg = fitz.Font(fontfile=FONT_REGULAR_PATH)
    font_bold = fitz.Font(fontfile=FONT_BOLD_PATH)

    # --- Page 1 ---
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    tw = fitz.TextWriter(page.rect)

    y = MARGIN_TOP

    # Company name
    tw.append((MARGIN_LEFT, y + 10), cfg["name"], font=font_bold, fontsize=11)
    y += 22

    # Contact lines
    for line in [
        f"мтс тел.: {cfg['phone']}",
        f"e-mail: {cfg['email']}",
        cfg["license"],
        cfg["accreditation"],
    ]:
        tw.append((MARGIN_LEFT, y + 9), line, font=font_reg, fontsize=8)
        y += 11

    y += 10
    tw.append((MARGIN_LEFT, y + 10), date_str, font=font_reg, fontsize=10)
    y += 22

    # Title
    title = (
        "Коммерческое предложение на комплекс работ по повышению предела огнестойкости "
        f"металлоконструкций на объекте: {object_name}"
    )
    tw.append((MARGIN_LEFT, y + 10), title, font=font_bold, fontsize=10)
    y += 24

    tw.write_text(page)
    tw = fitz.TextWriter(page.rect)

    # Table header
    headers = [
        "№\nп/п", "Наименование работ и затрат", "Количество", "Ед.\nизм.",
        "Цена за ед.\nбез НДС,\nруб.", "Стоимость без\nНДС, руб.",
        "НДС 22%,\nруб.", "Стоимость с\nНДС, руб.",
    ]
    header_h = 34
    header_fontsize = 6.5

    for i in range(8):
        x = col_positions[i]
        w = col_widths[i]
        rect = fitz.Rect(x, y, x + w, y + header_h)
        page.draw_rect(rect, color=(0.5, 0.5, 0.5), width=0.5)

    tw2 = fitz.TextWriter(page.rect)
    for i, hdr_text in enumerate(headers):
        x = col_positions[i]
        lines = hdr_text.split("\n")
        ty = y + 3
        for line in lines:
            tw2.append((x + 2, ty + header_fontsize), line, font=font_reg, fontsize=header_fontsize)
            ty += header_fontsize + 1
    tw2.write_text(page)

    y += header_h

    # Table rows
    total_wo_vat = Decimal("0")
    for i, item in enumerate(row_data):
        row_h = 14
        name = item.get("name", "")
        if name.count("\n") > 0:
            row_h = 28

        y_bottom = y + row_h
        for ci in range(8):
            rect = fitz.Rect(col_positions[ci], y, col_positions[ci + 1], y_bottom)
            page.draw_rect(rect, color=(0.6, 0.6, 0.6), width=0.3)

        tw3 = fitz.TextWriter(page.rect)

        tw3.append((col_positions[0] + 3, y + 10), str(i + 1), font=font_reg, fontsize=8)

        name_lines = name.split("\n")
        ny = y + 9
        for line in name_lines:
            tw3.append((col_positions[1] + 2, ny), line, font=font_reg, fontsize=7.5)
            ny += 9

        tw3.append((col_positions[2] + 3, y + 10), str(item.get("quantity", "")), font=font_reg, fontsize=8)
        tw3.append((col_positions[3] + 3, y + 10), str(item.get("unit", "")), font=font_reg, fontsize=8)
        tw3.append((col_positions[4] + 3, y + 10), str(item.get("price_per_unit", "")), font=font_reg, fontsize=8)
        tw3.append((col_positions[5] + 3, y + 10), str(item.get("cost_without_vat", "")), font=font_reg, fontsize=8)
        tw3.append((col_positions[6] + 3, y + 10), str(item.get("vat_amount", "")), font=font_reg, fontsize=8)
        tw3.append((col_positions[7] + 3, y + 10), str(item.get("cost_with_vat", "")), font=font_bold, fontsize=8)

        tw3.write_text(page)
        y = y_bottom

        try:
            cost_wo = str(item.get("cost_without_vat", "0")).replace(" ", "").replace("₽", "").replace(",", ".").replace("\u202f", "")
            total_wo_vat += Decimal(cost_wo)
        except Exception:
            pass

    total_vat = total_wo_vat * VAT_RATE / Decimal("100")
    total_w_vat = total_wo_vat + total_vat

    y += 4
    totals = [
        ("ИТОГО СТОИМОСТЬ РАБОТ БЕЗ НДС:", _fmt_price(total_wo_vat) if total_wo_vat > 0 else ""),
        ("НДС 22%:", _fmt_price(total_vat) if total_vat > 0 else ""),
        ("ИТОГО СТОИМОСТЬ РАБОТ С НДС:", _fmt_price(total_w_vat) if total_w_vat > 0 else ""),
    ]

    tw4 = fitz.TextWriter(page.rect)
    for label, value in totals:
        tw4.append((col_positions[5], y), label, font=font_reg, fontsize=9)
        tw4.append((col_positions[7] - 8, y), value, font=font_bold, fontsize=9)
        y += 16
    tw4.write_text(page)

    y += 8
    conditions = [
        f"- Гарантия на выполненные работы {cfg['guarantee_years']} лет",
        f"- Производство работ {cfg['workers_count']} человек",
        "- В стоимость включены оборудование для выполнения работ, вышки туры, перебазировка оборудования и людей",
        f"- Условия оплаты: {cfg['payment_terms']}",
        f"- При выполнении работ вы получаете полный комплект документов: {cfg['documents_package']}",
    ]
    tw5 = fitz.TextWriter(page.rect)
    for line in conditions:
        tw5.append((MARGIN_LEFT, y), line, font=font_reg, fontsize=7.5)
        y += 12
    tw5.write_text(page)

    # --- Page 2: Logo ---
    page2 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    if LOGO_PATH.exists():
        try:
            img_rect = fitz.Rect(60, 60, PAGE_WIDTH - 60, PAGE_HEIGHT - 60)
            page2.insert_image(img_rect, filename=str(LOGO_PATH), keep_proportion=True)
        except Exception as e:
            logger.warning(f"Logo insert failed: {e}")

    # --- Page 3: Stamp ---
    page3 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    if STAMP_PATH.exists():
        try:
            img_rect = fitz.Rect(100, 100, PAGE_WIDTH - 100, PAGE_HEIGHT - 100)
            page3.insert_image(img_rect, filename=str(STAMP_PATH), keep_proportion=True)
        except Exception as e:
            logger.warning(f"Stamp insert failed: {e}")

    pdf_bytes = doc.tobytes(deflate=True, garbage=4, clean=True)
    doc.close()
    return pdf_bytes
