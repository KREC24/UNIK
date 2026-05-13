"""
Парсер листа «Общие данные» (л.1 КМД).

Извлекает:
- Метаданные проекта (шифр, объект, стадия)
- Сводную таблицу металлопрофилей (профиль, ГОСТ, масса, марка стали)
- Ссылки на нормативные документы (СП, ГОСТ)
"""

import re
import logging
import pdfplumber
from pathlib import Path

from .parser_engine import BaseParser

logger = logging.getLogger(__name__)

STEEL_PROFILE_PATTERN = re.compile(
    r"(I\d{2}[А-ЯA-Z]\d|[А-ЯA-Z]\d{2,3}[xх×]\d{1,3}[xх×]?\d{0,3}|"
    r"\[?\d{2,3}[А-ЯA-Z]?\]?|"
    r"O\d{2}|"
    r"Гн[.·]\d{2,4}[xх×]\d{2,4}[xх×]\d|[ГL]\d{2,3}[xх×]\d{2,3}[xх×]?\d{0,3})"
)
GOST_PATTERN = re.compile(r"(ГОСТ|ГОСТ)\s*\S*\s*\d{2,6}[-.]\d{2,4}")
PROJECT_CODE_PATTERN = re.compile(
    r"[ВB]\d{5,7}[\/\\]\d{3,5}[А-ЯA-Z]?[-.]\d{3}[-.]\d{5}[-.]\d{2}[-.]\d{1,2}[.,]\d[-.][А-ЯA-Z]+"
)


class GeneralDataParser(BaseParser):
    """Парсер Общих данных (л.1)."""

    REQUIRED_FIELDS = ["profile_name"]
    OPTIONAL_FIELDS = ["gost_code", "steel_grade", "unit_weight_kg", "section_type"]

    def extract_text(self) -> str:
        try:
            with pdfplumber.open(self.source_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                return "\n".join(pages_text)
        except Exception as e:
            logger.exception("Ошибка чтения PDF: %s", e)
            return ""

    def detect_tables(self, text: str) -> list[list[str]]:
        return [text.split("\n")]

    def parse_rows(self, table_lines: list[str]) -> list[dict]:
        items = []
        for line in table_lines:
            profile_match = STEEL_PROFILE_PATTERN.search(line)
            if not profile_match:
                continue

            profile_name = profile_match.group(0)
            gost_match = GOST_PATTERN.search(line)
            gost_code = gost_match.group(0) if gost_match else None

            numbers = re.findall(r"(\d+[.,]\d+)", line)
            weight = float(numbers[0].replace(",", ".")) if numbers else None

            grade_match = re.search(r"[СC]\d{3}[-.]?\d?", line)
            steel_grade = grade_match.group(0) if grade_match else None

            section_type = self._classify_profile(profile_name)

            items.append({
                "profile_name": profile_name,
                "gost_code": gost_code,
                "steel_grade": steel_grade,
                "unit_weight_kg": weight,
                "section_type": section_type,
                "confidence": 0.85,
            })
        return items

    def extract_metadata(self, text: str) -> dict:
        metadata = {}
        project_match = PROJECT_CODE_PATTERN.search(text)
        if project_match:
            metadata["project_code"] = project_match.group(0)

        object_match = re.search(
            r"(?:объект[ае]?|строительств[ао])\s*[：:]\s*(.+?)(?:\n|$)",
            text, re.IGNORECASE,
        )
        if object_match:
            metadata["object_name"] = object_match.group(1).strip()

        stage_match = re.search(r"(?:стадия)\s*[：:—–-]\s*([А-ЯA-Z]+)", text, re.IGNORECASE)
        if stage_match:
            metadata["stage"] = stage_match.group(1)

        return metadata

    @staticmethod
    def _classify_profile(name: str) -> str:
        name_upper = name.upper()
        if name_upper.startswith("I") and any(c.isdigit() for c in name_upper):
            return "beam"
        if name_upper.startswith("[") or "П" in name_upper:
            return "channel"
        if name_upper.startswith("L") or "УГОЛ" in name_upper:
            return "angle"
        if name_upper.startswith("O") or "КРУГ" in name_upper:
            return "round"
        if "X" in name_upper or "Х" in name_upper:
            if "ГН" in name_upper or "ТРУБ" in name_upper:
                return "pipe"
        if "ЛИСТ" in name_upper or "ГН" in name_upper:
            return "bent_section"
        return "other"
