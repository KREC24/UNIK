"""
Специализированный парсер «Ведомости отправочных марок» (л.2 КМД).

Формат листа: 6-колоночный дублированный блок.
Каждая строка содержит до 6 элементов, каждый по 11 полей:
Поз | Марка | Описание | Кол-во | X | Y | Z | Масса ед. | Масса общ. | S ед. | S общ.

Особенности извлечения:
- Текст из PDF извлекается через pdfplumber
- Таблица детектируется по ключевым словам в заголовке
- Строки разбиваются на чанки по паттерну «число → марка → слово → число → 3×число → 2×float → 2×float»
- Игнорируются строки-заголовки и итоговые строки
"""

import re
import logging
import pdfplumber
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Optional

from .parser_engine import BaseParser, ParseResult

logger = logging.getLogger(__name__)

MARK_PATTERN = re.compile(r"^[A-ZА-Я][A-ZА-Я0-9]*([.-][0-9]+)+$|^[A-ZА-Я]+[-\s]?[0-9]+$")
DIMENSION_PATTERN = re.compile(r"^\d{1,5}$")
FLOAT_PATTERN = re.compile(r"^\d+([.,]\d+)?$")
INT_PATTERN = re.compile(r"^\d+$")
SUMMARY_PATTERN = re.compile(r"^(ИТОГО|ВСЕГО|∑|ВСЕГО ПО)", re.IGNORECASE)
SKIP_WORDS = {
    "Ведомость", "отправочных", "марок", "Габарит", "Масса", "Площадь",
    "Лист", "Поз", "Марка", "Описание", "Кол-во", "Одной", "Всех",
    "мм", "кг", "м2", "X", "Y", "Z", "Прим.",
}

RUSSIAN_TYPE_NAMES = {
    "рама": "Рама", "балка": "Балка", "колонна": "Колонна",
    "стойка": "Стойка", "связь": "Связь", "ферма": "Ферма",
    "козырек": "Козырек", "ограждение": "Ограждение",
    "распорка": "Распорка", "стремянка": "Стремянка",
    "прогон": "Прогон", "ребро": "Ребро", "упор": "Упор",
    "монтажная": "Монтажная", "деталь": "Деталь",
    "лестница": "Лестница", "рельс": "Рельс", "стропило": "Стропило",
    "нащельник": "Нащельник", "фланец": "Фланец",
    "косынка": "Косынка", "планка": "Планка", "швеллер": "Швеллер",
    "уголок": "Уголок", "труба": "Труба", "лист": "Лист",
}


def _normalize_number(s: str) -> Optional[float]:
    s = s.replace(",", ".").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return None


def _is_mark(token: str) -> bool:
    return bool(MARK_PATTERN.match(token)) and len(token) >= 3


def _is_dimension(token: str) -> bool:
    return bool(DIMENSION_PATTERN.match(token)) and 3 <= int(token) <= 25000


def _is_float(token: str) -> bool:
    return bool(FLOAT_PATTERN.match(token.replace(",", ".")))


def _is_int(token: str) -> bool:
    return bool(INT_PATTERN.match(token))


STEEL_DENSITY_MM = Decimal("7.85")


def _calc_ptm(item: dict) -> None:
    """Автоматически рассчитывает приведённую толщину металла (PTM)."""
    if item.get("ptm") is not None:
        return
    try:
        mass = item.get("total_weight_kg") or item.get("unit_weight_kg")
        area = item.get("total_area_m2") or item.get("unit_area_m2")
        if mass is not None and area is not None:
            m = Decimal(str(mass))
            a = Decimal(str(area))
            if a > 0:
                item["ptm"] = float((m / (a * STEEL_DENSITY_MM)).quantize(Decimal("0.01")))
                return
    except (InvalidOperation, ValueError, TypeError):
        pass
    item["ptm"] = None


class KmdShippingParser(BaseParser):
    """Парсер ведомости отправочных марок (л.2 КМД)."""

    REQUIRED_FIELDS = ["mark", "quantity"]
    OPTIONAL_FIELDS = [
        "position", "type_name", "length_x", "width_y", "height_z",
        "unit_weight_kg", "unit_area_m2", "total_area_m2",
    ]
    TABLE_HEADER_KEYWORDS = [
        "Ведомость", "отправочных", "марок", "Габарит", "Масса",
    ]

    def __init__(self, source_path: Path | str):
        super().__init__(source_path)
        self._raw_text: str = ""

    def extract_text(self) -> str:
        try:
            with pdfplumber.open(self.source_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                self._raw_text = "\n".join(pages_text)
        except Exception as e:
            logger.exception("Ошибка чтения PDF: %s", e)
            return ""
        return self._raw_text

    def detect_tables(self, text: str) -> list[list[str]]:
        """Обнаруживает строки таблицы: фильтрует текст, оставляя только строки с данными."""
        lines = text.split("\n")
        table_lines = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if any(kw.lower() in stripped.lower() for kw in self.TABLE_HEADER_KEYWORDS):
                in_table = True
                continue

            if SUMMARY_PATTERN.search(stripped):
                continue

            if in_table:
                tokens = stripped.split()
                numeric_count = sum(1 for t in tokens if _is_int(t) or _is_float(t))
                if numeric_count >= 3 and len(tokens) >= 6:
                    table_lines.append(stripped)

        return [table_lines] if table_lines else []

    def _split_into_chunks(self, tokens: list[str]) -> list[list[str]]:
        """Разбивает линейный поток токенов на чанки по 11 полей на элемент."""
        chunks = []
        i = 0
        while i < len(tokens):
            start = i
            sequence = []
            state = "position"

            while i < len(tokens):
                token = tokens[i]
                if state == "position":
                    if _is_int(token) and 1 <= int(token) <= 999:
                        sequence.append(int(token))
                        state = "mark"
                        i += 1
                    else:
                        break
                elif state == "mark":
                    if _is_mark(token):
                        sequence.append(token)
                        state = "type_name"
                        i += 1
                    elif _is_int(token) and len(sequence) == 1:
                        i = start
                        break
                    else:
                        break
                elif state == "type_name":
                    if token.lower() in RUSSIAN_TYPE_NAMES or (
                        not _is_int(token) and not _is_float(token) and not _is_mark(token)
                    ):
                        name = RUSSIAN_TYPE_NAMES.get(token.lower(), token)
                        sequence.append(name)
                        # Look ahead for multi-word type names (Монтажная деталь, Линейный извещатель...)
                        if i + 1 < len(tokens):
                            next_t = tokens[i + 1]
                            if (not _is_int(next_t) and not _is_float(next_t)
                                    and not _is_mark(next_t) and len(next_t) > 1):
                                state = "type_name_cont"
                            else:
                                state = "quantity"
                        else:
                            state = "quantity"
                        i += 1
                    else:
                        break
                elif state == "type_name_cont":
                    if not _is_int(token) and not _is_float(token) and not _is_mark(token):
                        sequence[-1] = sequence[-1] + " " + token
                        if i + 1 < len(tokens):
                            next_t = tokens[i + 1]
                            if (not _is_int(next_t) and not _is_float(next_t)
                                    and not _is_mark(next_t) and len(next_t) > 1):
                                state = "type_name_cont"
                            else:
                                state = "quantity"
                        else:
                            state = "quantity"
                        i += 1
                    else:
                        state = "quantity"
                elif state == "quantity":
                    if _is_int(token):
                        sequence.append(int(token))
                        state = "dims"
                        i += 1
                    else:
                        break
                elif state == "dims":
                    dims = []
                    for _ in range(3):
                        if i < len(tokens) and _is_dimension(tokens[i]):
                            dims.append(int(tokens[i]))
                            i += 1
                    if len(dims) == 3:
                        sequence.extend(dims)
                        state = "masses"
                    else:
                        i = start + 1
                        break
                elif state == "masses":
                    masses = []
                    for _ in range(2):
                        if i < len(tokens) and _is_float(tokens[i]):
                            masses.append(_normalize_number(tokens[i]))
                            i += 1
                    if len(masses) == 2:
                        sequence.extend(masses)
                        state = "areas"
                    else:
                        i = start + 1
                        break
                elif state == "areas":
                    areas = []
                    for _ in range(2):
                        if i < len(tokens) and _is_float(tokens[i]):
                            areas.append(_normalize_number(tokens[i]))
                            i += 1
                    if len(areas) == 2:
                        sequence.extend(areas)
                        state = "done"
                    elif len(areas) == 0:
                        state = "done"
                    else:
                        state = "done"
                    if state == "done":
                        break

            if len(sequence) >= 5:
                chunks.append(sequence)
            i = max(i, start + 1)

        return chunks

    def _chunk_to_dict(self, chunk: list) -> dict:
        """Преобразует чанк [pos, mark, name, qty, x, y, z, m1, m2, s1, s2] в словарь."""
        item: dict = {
            "mark": None, "type_name": None, "quantity": None,
            "length_x": None, "width_y": None, "height_z": None,
            "unit_weight_kg": None, "total_weight_kg": None,
            "unit_area_m2": None, "total_area_m2": None, "position": None,
            "ptm": None,
        }

        idx = 0
        if len(chunk) > idx and isinstance(chunk[idx], int):
            item["position"] = chunk[idx]; idx += 1
        if len(chunk) > idx and isinstance(chunk[idx], str):
            item["mark"] = chunk[idx]; idx += 1
        if len(chunk) > idx and isinstance(chunk[idx], str):
            item["type_name"] = chunk[idx]; idx += 1
        if len(chunk) > idx and isinstance(chunk[idx], int):
            item["quantity"] = chunk[idx]; idx += 1
        if len(chunk) > idx + 2:
            if all(isinstance(chunk[idx + j], int) for j in range(3)):
                item["length_x"] = chunk[idx]
                item["width_y"] = chunk[idx + 1]
                item["height_z"] = chunk[idx + 2]
                idx += 3
        if len(chunk) > idx + 1:
            if all(isinstance(chunk[idx + j], (int, float)) for j in range(2)):
                item["unit_weight_kg"] = chunk[idx]
                item["total_weight_kg"] = chunk[idx + 1]
                idx += 2
        if len(chunk) > idx + 1:
            if all(isinstance(chunk[idx + j], (int, float)) for j in range(2)):
                item["unit_area_m2"] = chunk[idx]
                item["total_area_m2"] = chunk[idx + 1]

        _calc_ptm(item)

        return item

    def parse_rows(self, table_lines: list[str]) -> list[dict]:
        items = []
        for line in table_lines:
            tokens = line.split()
            if not tokens:
                continue
            if SUMMARY_PATTERN.search(line):
                continue

            chunks = self._split_into_chunks(tokens)
            for chunk in chunks:
                item = self._chunk_to_dict(chunk)
                if item["mark"] and item["quantity"]:
                    items.append(item)

        return items

    def extract_metadata(self, text: str) -> dict:
        metadata = {}
        project_match = re.search(
            r"[ВBВ]\d{5,7}[\/\\]\d{3,5}[А-ЯA-Z]?[-.]\d{3}[-.]\d{5}[-.]\d{2}[-.]\d{1,2}[.,]\d[-.][А-ЯA-Z]+",
            text,
        )
        if project_match:
            metadata["project_code"] = project_match.group(0)
        return metadata
