"""
Парсер 34-страничного пакета КМД revC04.

Извлекает:
1. Элементы из «Ведомость элементов» (стр. 7)
2. Профили стали из «Техническая спецификация стали» (стр. 22, 27, 31)
3. Метаданные
"""

import re
import logging
from pathlib import Path
from typing import Optional

import pdfplumber

from .parser_engine import BaseParser, ParseResult

logger = logging.getLogger(__name__)


def _repair_encoding(text: str) -> str:
    """Ремонт кодировки: latin-1-интерпретированная cp1251 кириллица."""
    cyrillic_count = sum(1 for ch in text if '\u0400' <= ch <= '\u04FF')
    if cyrillic_count > 5:
        return text
    high_latin = sum(1 for ch in text if '\u00C0' <= ch <= '\u00FF')
    if high_latin < 10:
        return text
    result = []
    for ch in text:
        if ord(ch) < 256:
            try:
                result.append(ch.encode('latin-1').decode('cp1251'))
            except (UnicodeEncodeError, UnicodeDecodeError):
                result.append(ch)
        else:
            result.append(ch)
    return ''.join(result)


PROFILE_PATTERN = re.compile(
    r"(I\d{2,3}[А-ЯA-Z]+\d*|"
    r"\[\d{2,3}[А-ЯA-Z]*|"
    r"L\d{2,3}[XХx]\d{1,3}|"
    r"Гн[з]?\d+[XХx]\d+[XХx]\d+|"
    r"Гн\[\d+[XХx]\d+[XХx]\d+|"
    r"[НH]\d{2,3}[-.]\d{3,4}[-.]\d[.,]\d|"
    r"[ØO]\d{2,3}|"
    r"SP\s+\d{2,3}[xXх]\d{2,4}/\d{2,3}[xXх]\d[^\s,]*|"
    r"[—–-]\s*\d+[.,]?\d*\s*мм)",
    re.IGNORECASE,
)

STEEL_GRADE_RE = re.compile(r"[СC](\d{3})[-.](\d)", re.IGNORECASE)
GOST_RE = re.compile(r"ГОСТ\s+([\d\-]+)", re.IGNORECASE)
PROJECT_CODE_RE = re.compile(
    r"[ВB]\d{5,7}[/\\]\d{3,5}[А-ЯA-Z]?[-.]\d{3}[-.]\d{5}[-.]\d{2}[-.]\d{1,2}[.,]\d[-.][А-ЯA-Z]+",
)
MARK_LINE_RE = re.compile(
    r"^([A-ZА-Я][A-ZА-Я0-9]{0,4}[\d.]+)\s+(I\d{2}|\[\d{2}|L\d{2,3}[XХx]|Гн[з]?|SP\s)",
    re.IGNORECASE,
)

NON_MARK_TOKENS = {
    "вид", "сложный", "тавр", "лист", "решетчатый",
    "сложн", "решет", "решетч", "слож",
    "изм", "зам", "нов", "гост", "всего",
    "а", "б", "в", "г", "д", "е", "1", "2", "3", "4", "5",
    "сп1",  # "вид СП1" — СП1 appears after "вид" label
}

SECTION_HEADERS = re.compile(
    r"(Ведомость\s+элементов|Ведомость\s+рабочих\s+чертежей|"
    r"Техническая\s+спецификация\s+стали|"
    r"Сбор\s+нагрузок|Схема\s+расположения|"
    r"Разрез|Фасад|Геометрическая\s+схема|"
    r"Узел\s+\d|Схема\s+раскладки|"
    r"Схема\s+размещения)",
    re.IGNORECASE,
)

ELEMENTS_HEADER = re.compile(r"Ведомость\s+элементов", re.IGNORECASE)
SPEC_HEADER = re.compile(r"Техническая\s+спецификация\s+стали", re.IGNORECASE)

FOOTER_PATTERNS = re.compile(
    r"(В068522|B068522|Всего\s+массы|Стадия\s+Лист|"
    r"ГИП\s+Батищева|Проверил\s+Двойников|Разработал\s+Соколов|"
    r"Н.Контроль\s+Комиссаров|Изм\.\s+Кол\.уч\.|"
    r"Лист\s+Листов)",
    re.IGNORECASE,
)

SKIP_DATA_LINES = re.compile(
    r"^(Марка|Ведомость|Всего|ГОСТ\s|ГИП|"
    r"Проверил|Разработал|Н.Контроль|"
    r"Стадия|Лист\s+Листов|Изм\.\s+Кол|"
    r"1\s+2\s+3\s+4\s+5|"
    r"^(Масса|Номер|Наименование)\s)",
    re.IGNORECASE,
)


def _classify_profile(profile_str: str) -> Optional[str]:
    if not profile_str:
        return None
    p = profile_str.strip().upper().replace("Х", "X")
    if re.match(r"^I\d{2,3}[А-ЯA-Z]+\d*$", p, re.IGNORECASE):
        return "двутавр"
    if re.search(r"\[\d{2,3}[А-ЯA-Z]*$", p):
        return "швеллер"
    if re.match(r"^L\d{2,3}X\d{1,3}$", p):
        return "уголок"
    if re.match(r"^ГН[З]?\d+[XХ]\d+[XХ]\d+$", p):
        return "труба"
    if re.match(r"^ГН\[\d+[XХ]\d+[XХ]\d+$", p):
        return "швеллер гнутый"
    if re.match(r"^[НH]\d{2,3}[-.]\d{3,4}[-.]\d[.,]\d$", p):
        return "профнастил"
    if re.match(r"^[ØO]\d{2,3}$", p):
        return "круг"
    if re.match(r"^[—–-]?\s*\d+[.,]?\d*\s*ММ$", p, re.IGNORECASE):
        return "лист"
    if re.search(r"ТАВР", p, re.IGNORECASE) or re.search(r"ИЗ\s*I\d", p, re.IGNORECASE):
        return "тавр"
    if re.match(r"^SP\s+\d", p, re.IGNORECASE):
        return "настил решетчатый"
    return "прочее"


def _extract_steel_grade(text: str) -> Optional[str]:
    m = STEEL_GRADE_RE.search(text)
    if m:
        return f"С{m.group(1)}-{m.group(2)}"
    return None


def _deduplicate(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for p in items:
        key = (p.get("profile_name") or p.get("ogz_notes"),
               p.get("gost_code"), p.get("steel_grade"), p.get("mark"))
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


class RevC04Parser(BaseParser):
    """Парсер пакета КМД revC04 (34 стр.)."""

    REQUIRED_FIELDS = ["mark", "profile_type"]
    OPTIONAL_FIELDS = [
        "type_name", "quantity", "length_x", "width_y", "height_z",
        "unit_weight_kg", "total_weight_kg", "unit_area_m2", "total_area_m2",
        "steel_grade", "gost_code",
    ]

    def __init__(self, source_path: Path | str):
        super().__init__(source_path)
        self._raw_text: str = ""
        self._all_profiles: list[dict] = []

    def extract_text(self) -> str:
        try:
            with pdfplumber.open(self.source_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(_repair_encoding(t))
                self._raw_text = "\n".join(pages_text)
        except Exception as e:
            logger.exception("Ошибка чтения PDF: %s", e)
            return ""
        return self._raw_text

    def detect_tables(self, text: str) -> list[list[str]]:
        lines = text.split("\n")
        tables: list[list[str]] = []
        current_table: list[str] = []
        in_section = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if SECTION_HEADERS.search(stripped):
                if current_table:
                    tables.append(current_table)
                    current_table = []
                if ELEMENTS_HEADER.search(stripped) or SPEC_HEADER.search(stripped):
                    in_section = True
                else:
                    in_section = False
                continue

            if in_section and FOOTER_PATTERNS.search(stripped):
                if current_table:
                    tables.append(current_table)
                    current_table = []
                in_section = False
                continue

            if in_section:
                if SKIP_DATA_LINES.match(stripped):
                    continue
                if re.match(r"^\s*(?:мм|ìì|ýëåìåíòà|профиля|ïðîôèëÿ)\s*$", stripped):
                    continue
                if len(stripped) < 3:
                    continue

                has_mark = MARK_LINE_RE.match(stripped)
                has_profile = PROFILE_PATTERN.search(stripped)
                has_gost = GOST_RE.search(stripped)
                has_steel = STEEL_GRADE_RE.search(stripped)
                has_plate = re.search(r"[—–-]\s*\d+[.,]?\d*\s*мм", stripped)

                if has_mark or has_profile or has_gost or has_steel or has_plate:
                    current_table.append(stripped)
                elif current_table and re.search(r"\d", stripped):
                    current_table.append(stripped)

        if current_table:
            tables.append(current_table)

        return tables

    def parse_rows(self, table_lines: list[str]) -> list[dict]:
        items: list[dict] = []
        full_text = "\n".join(table_lines)

        element_items = self._parse_element_lines(table_lines)
        spec_items = self._parse_spec_lines(table_lines)

        seen_marks = set()
        seen_profiles = set()
        for ei in element_items:
            key = ei.get("mark")
            if key and key not in seen_marks:
                seen_marks.add(key)
                items.append(ei)

        for si in spec_items:
            pn = si.get("ogz_notes", "")
            if not pn:
                continue
            if pn in seen_profiles:
                continue
            found = False
            for it in items:
                if it.get("ogz_notes") == pn:
                    if si.get("steel_grade") and not it.get("steel_grade"):
                        it["steel_grade"] = si["steel_grade"]
                    if si.get("gost_code") and not it.get("gost_code"):
                        it["gost_code"] = si["gost_code"]
                    found = True
                    break
            if not found:
                seen_profiles.add(pn)
                items.append(si)

        return items

    def _parse_element_lines(self, lines: list[str]) -> list[dict]:
        items = []
        for line in lines:
            stripped = line.strip()
            if not stripped or SKIP_DATA_LINES.match(stripped):
                continue
            if GOST_RE.search(stripped):
                continue

            tokens = stripped.split()
            if len(tokens) < 3:
                continue

            mark = None
            profile = None
            steel = None

            mm = MARK_LINE_RE.match(stripped)
            if mm:
                mark = mm.group(1)
            else:
                first = tokens[0]
                first_clean = first.strip().rstrip(".")
                if first_clean.lower() in NON_MARK_TOKENS:
                    continue
                if re.match(r"^[A-ZА-Я][A-ZА-Я0-9]*[\d.]+$", first, re.IGNORECASE):
                    if PROFILE_PATTERN.match(first):
                        continue
                    mark = first
                elif re.match(r"^\d+[A-ZА-Я]*$", first, re.IGNORECASE):
                    if len(tokens) > 1 and re.match(r"^[A-ZА-Я]", tokens[1], re.IGNORECASE):
                        candidate = tokens[1].strip().rstrip(".")
                        if (not PROFILE_PATTERN.match(candidate)
                                and candidate.lower() not in NON_MARK_TOKENS):
                            mark = candidate

            pm = PROFILE_PATTERN.search(stripped)
            if pm:
                profile = pm.group(1)

            for token in tokens:
                sg = _extract_steel_grade(token)
                if sg:
                    steel = sg
                    break

            if mark and profile:
                section_type = _classify_profile(profile)
                items.append({
                    "mark": mark,
                    "type_name": section_type,
                    "profile_type": section_type,
                    "steel_grade": steel,
                    "position": None,
                    "quantity": None,
                    "length_x": None,
                    "width_y": None,
                    "height_z": None,
                    "unit_weight_kg": None,
                    "total_weight_kg": None,
                    "unit_area_m2": None,
                    "total_area_m2": None,
                    "ogz_notes": profile,
                    "gost_code": None,
                })

        return items

    def _parse_spec_lines(self, lines: list[str]) -> list[dict]:
        profiles: list[dict] = []
        current_gost: Optional[str] = None
        current_steel: Optional[str] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.search(r"Всего\s+(?:профиля|массы)", stripped):
                continue

            gm = GOST_RE.search(stripped)
            if gm:
                current_gost = f"ГОСТ {gm.group(1)}"

            sm = STEEL_GRADE_RE.search(stripped)
            if sm:
                if re.search(r"^[—–-]\s*\d", stripped):
                    pass
                else:
                    current_steel = f"С{sm.group(1)}-{sm.group(2)}"

            pm = PROFILE_PATTERN.search(stripped)
            if pm:
                pname = pm.group(1)
                stype = _classify_profile(pname)
                gost = current_gost
                steel = current_steel
                if "лист" in stype and not gost:
                    gost = "ГОСТ 19903-2015"
                profiles.append({
                    "mark": None,
                    "type_name": stype,
                    "profile_type": stype,
                    "steel_grade": steel,
                    "position": None,
                    "quantity": None,
                    "length_x": None, "width_y": None, "height_z": None,
                    "unit_weight_kg": None, "total_weight_kg": None,
                    "unit_area_m2": None, "total_area_m2": None,
                    "ogz_notes": pname,
                    "gost_code": gost,
                })

        self._all_profiles = _deduplicate(profiles)
        return profiles

    def extract_metadata(self, text: str) -> dict:
        metadata: dict = {}

        m = PROJECT_CODE_RE.search(text)
        if m:
            metadata["project_code"] = m.group(0)

        revisions = []
        seen_keys = set()
        for m in re.finditer(
            r"(\d+)\s+(?:Зам\.?|Нов\.?)?\s*(\d{2,3}[-.]\d{2,3})?\s*(\d{2}\.\d{2})",
            text,
        ):
            rev_num = m.group(1)
            rev_code = m.group(2) or ""
            rev_date = m.group(3) or ""
            if not rev_date:
                continue
            key = (rev_num, rev_code)
            if key not in seen_keys and int(rev_num) <= 10:
                seen_keys.add(key)
                revisions.append({
                    "number": rev_num,
                    "code": rev_code,
                    "date": rev_date,
                })

        metadata["revisions"] = revisions

        if re.search(r"Корпоративный\s+учебный\s+центр", text):
            metadata["object_name"] = (
                "Корпоративный учебный центр в г. Красноярске. "
                "1 этап строительства. Полигон практического тренинга"
            )

        metadata["stage"] = "КМ"
        return metadata

    def parse(self) -> ParseResult:
        try:
            text = self.extract_text()
            if not text:
                self.result.errors.append("Не удалось извлечь текст из PDF")
                return self.result

            self.result.metadata = self.extract_metadata(text)
            tables = self.detect_tables(text)

            all_items = []
            unrecognized = []
            for table_lines in tables:
                for item in self.parse_rows(table_lines):
                    is_valid, issues = self.validate_row(item)
                    if is_valid:
                        item["confidence"] = 1.0
                        all_items.append(item)
                    else:
                        item["confidence"] = 0.0
                        item["issues"] = issues
                        unrecognized.append(item)

            all_items = _deduplicate(all_items)
            self.result.items = all_items
            self.result.unrecognized_rows = unrecognized
            self.result.total_rows_parsed = len(all_items)
            self.result.total_rows_raw = len(all_items) + len(unrecognized)

            if self._all_profiles:
                self.result.metadata["steel_profiles_count"] = len(self._all_profiles)

            logger.info(
                "Парсинг revC04: %d элементов, %d профилей стали",
                self.result.total_rows_parsed,
                len(self._all_profiles),
            )
        except Exception as e:
            logger.exception("Ошибка парсинга %s", self.source_path)
            self.result.errors.append(str(e))

        return self.result
