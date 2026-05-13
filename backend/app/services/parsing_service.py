import logging
from pathlib import Path
from typing import Optional

from app.core.kmd_parser import KmdShippingParser
from app.core.general_data_parser import GeneralDataParser
from app.core.parser_engine import ParseResult
from app.schemas.parser import (
    LineItemSchema, UnrecognizedRowSchema,
    MetadataSchema, ParseResultSchema,
)

logger = logging.getLogger(__name__)


def _result_to_schema(result: ParseResult) -> ParseResultSchema:
    items = [
        LineItemSchema(
            position=item.get("position"),
            mark=item.get("mark"),
            type_name=item.get("type_name"),
            quantity=item.get("quantity"),
            length_x=item.get("length_x"),
            width_y=item.get("width_y"),
            height_z=item.get("height_z"),
            unit_weight_kg=item.get("unit_weight_kg"),
            total_weight_kg=item.get("total_weight_kg"),
            unit_area_m2=item.get("unit_area_m2"),
            total_area_m2=item.get("total_area_m2"),
            ogz_notes=item.get("ogz_notes"),
            profile_type=item.get("profile_type"),
            steel_grade=item.get("steel_grade"),
            gost_code=item.get("gost_code"),
            confidence=item.get("confidence", 1.0),
        )
        for item in result.items
    ]
    unrecognized = [
        UnrecognizedRowSchema(
            raw_text=row.get("raw_text", str(row)),
            partial_data={k: v for k, v in row.items() if v is not None},
            issues=row.get("issues", []),
        )
        for row in result.unrecognized_rows
    ]
    metadata = MetadataSchema(
        project_code=result.metadata.get("project_code"),
        object_name=result.metadata.get("object_name"),
        stage=result.metadata.get("stage"),
    )
    return ParseResultSchema(
        source_file=result.source_file,
        batch_type=result.batch_type,
        metadata=metadata,
        items=items,
        unrecognized_rows=unrecognized,
        errors=result.errors,
        total_rows_parsed=result.total_rows_parsed,
        total_rows_raw=result.total_rows_raw,
        success_rate=result.success_rate,
    )


def parse_shipping_list(file_path: Path) -> ParseResultSchema:
    """Парсинг ведомости отправочных марок (л.2)."""
    parser = KmdShippingParser(file_path)
    result = parser.parse()
    return _result_to_schema(result)


def parse_general_data(file_path: Path) -> ParseResultSchema:
    """Парсинг общих данных (л.1)."""
    parser = GeneralDataParser(file_path)
    result = parser.parse()
    return _result_to_schema(result)


def auto_detect_and_parse(file_path: Path) -> ParseResultSchema:
    """Автоопределение типа документа и парсинг."""
    name_lower = file_path.name.lower()
    if "ведомость" in name_lower or "отправочных" in name_lower or "марок" in name_lower or "л.2" in name_lower:
        return parse_shipping_list(file_path)
    if "общие" in name_lower or "общие данные" in name_lower or "л.1" in name_lower:
        return parse_general_data(file_path)
    return parse_shipping_list(file_path)
