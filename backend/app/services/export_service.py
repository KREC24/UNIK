import io
import json
import csv
from decimal import Decimal

import pandas as pd
from fastapi.responses import StreamingResponse

from app.schemas.parser import ParseResultSchema


def _decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def export_json(result: ParseResultSchema) -> StreamingResponse:
    data = {
        "source_file": result.source_file,
        "batch_type": result.batch_type,
        "metadata": result.metadata.model_dump(),
        "items": [
            {k: _decimal_to_float(v) for k, v in item.model_dump().items()}
            for item in result.items
        ],
        "unrecognized_rows": result.unrecognized_rows,
        "errors": result.errors,
        "success_rate": result.success_rate,
    }
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=parse_result.json"},
    )


def export_csv(result: ParseResultSchema) -> StreamingResponse:
    output = io.StringIO()
    fieldnames = [
        "position", "mark", "type_name", "quantity",
        "length_x", "width_y", "height_z",
        "unit_weight_kg", "total_weight_kg",
        "unit_area_m2", "total_area_m2",
        "ogz_notes", "steel_grade", "profile_type",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in result.items:
        row = {k: _decimal_to_float(v) for k, v in item.model_dump().items()}
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=parse_result.csv"},
    )


def export_xlsx(result: ParseResultSchema) -> StreamingResponse:
    rows = []
    for item in result.items:
        d = item.model_dump()
        rows.append({k: _decimal_to_float(v) for k, v in d.items()})

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ведомость марок")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=parse_result.xlsx"},
    )
