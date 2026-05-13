"""
Parser Engine — базовый модуль извлечения данных из PDF-документов.

Архитектура:
1. BaseParser — абстрактный класс с общими методами
2. Конвейер: PDF → текст → таблицы → строки → валидация → JSON
3. Модульный подход — каждый тип документа = класс-наследник
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    source_file: str
    batch_type: str
    items: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    unrecognized_rows: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_rows_parsed: int = 0
    total_rows_raw: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_rows_raw == 0:
            return 1.0
        return self.total_rows_parsed / self.total_rows_raw


class BaseParser(ABC):
    """Абстрактный парсер строительной документации."""

    REQUIRED_FIELDS: list[str] = []
    OPTIONAL_FIELDS: list[str] = []
    TABLE_HEADER_KEYWORDS: list[str] = []

    def __init__(self, source_path: Path | str):
        self.source_path = Path(source_path)
        self.result = ParseResult(
            source_file=self.source_path.name,
            batch_type=self.__class__.__name__,
        )

    @abstractmethod
    def extract_text(self) -> str:
        """Извлечь весь текст из PDF."""
        ...

    @abstractmethod
    def detect_tables(self, text: str) -> list[list[str]]:
        """Обнаружить таблицы в текстовом потоке."""
        ...

    @abstractmethod
    def parse_rows(self, table_lines: list[str]) -> list[dict]:
        """Разобрать строки таблицы в словари полей."""
        ...

    @abstractmethod
    def extract_metadata(self, text: str) -> dict:
        """Извлечь метаданные документа (проект, объект, стадия)."""
        ...

    def validate_row(self, item: dict) -> tuple[bool, list[str]]:
        """Валидация строки: наличие обязательных полей, корректность чисел."""
        issues = []
        for field in self.REQUIRED_FIELDS:
            if field not in item or item[field] is None:
                issues.append(f"Отсутствует обязательное поле: {field}")
        if "quantity" in item and item["quantity"] is not None:
            if item["quantity"] <= 0:
                issues.append(f"Некорректное количество: {item['quantity']}")
        if "total_weight_kg" in item and item["total_weight_kg"] is not None:
            if item["total_weight_kg"] < 0:
                issues.append(f"Отрицательная масса: {item['total_weight_kg']}")
        return len(issues) == 0, issues

    def parse(self) -> ParseResult:
        """Основной метод: запуск конвейера парсинга."""
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

            self.result.items = all_items
            self.result.unrecognized_rows = unrecognized
            self.result.total_rows_parsed = len(all_items)
            self.result.total_rows_raw = len(all_items) + len(unrecognized)

            logger.info(
                "Парсинг завершён: %d/%d строк распознано (%.1f%%)",
                self.result.total_rows_parsed,
                self.result.total_rows_raw,
                self.result.success_rate * 100,
            )
        except Exception as e:
            logger.exception("Ошибка парсинга %s", self.source_path)
            self.result.errors.append(str(e))

        return self.result
