"""Parser API routes — upload, parse, persist to DB."""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.config import settings, get_max_upload_size_mb
from app.schemas.parser import ParseResultSchema
from app.services.parsing_service import (
    parse_shipping_list, parse_general_data, parse_revC04, auto_detect_and_parse,
)
from app.services.export_service import export_json, export_csv, export_xlsx
from app.services.project_service import persist_batch_result, get_batch_from_db

router = APIRouter(prefix="/parse", tags=["Parser"])


@router.post("/upload", response_model=ParseResultSchema)
async def upload_pdf(
    file: UploadFile = File(...),
    parser_type: Optional[str] = Query(None, description="shipping | general | revC04 | auto"),
    project_id: Optional[str] = Query(None, description="UUID проекта для привязки"),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Принимаются только PDF-файлы")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = settings.UPLOAD_DIR / safe_name

    content = await file.read()
    if len(content) > get_max_upload_size_mb() * 1024 * 1024:
        raise HTTPException(400, f"Файл превышает {get_max_upload_size_mb()} МБ")

    file_path.write_bytes(content)

    try:
        if parser_type == "shipping":
            result = parse_shipping_list(file_path)
        elif parser_type == "general":
            result = parse_general_data(file_path)
        elif parser_type == "revC04":
            result = parse_revC04(file_path)
        else:
            result = auto_detect_and_parse(file_path)
    except Exception as e:
        raise HTTPException(500, f"Ошибка парсинга: {e}")

    batch_id = uuid.uuid4().hex
    await persist_batch_result(db, batch_id, result, project_id)

    return JSONResponse(
        content={
            **result.model_dump(),
            "batch_id": batch_id,
        },
    )


@router.get("/batches/{batch_id}")
async def get_batch_status(batch_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_batch_from_db(db, batch_id)
    if not data:
        raise HTTPException(404, "Пакет не найден")
    return JSONResponse(content=data)


@router.get("/batches/{batch_id}/preview")
async def preview_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_batch_from_db(db, batch_id)
    if not data:
        raise HTTPException(404, "Пакет не найден")
    return JSONResponse(content={
        "batch_id": batch_id,
        "source_file": data["source_file"],
        "status": data["status"],
        "total_items": data["total_items"],
        "items": data["items"][:100],
        "unrecognized_count": data["unrecognized_count"],
    })


@router.get("/batches/{batch_id}/export/json")
async def export_batch_json(batch_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_batch_from_db(db, batch_id)
    if not data:
        raise HTTPException(404, "Пакет не найден")
    import json
    import io
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=parse_result.json"},
    )


@router.get("/batches/{batch_id}/export/csv")
async def export_batch_csv(batch_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_batch_from_db(db, batch_id)
    if not data:
        raise HTTPException(404, "Пакет не найден")
    import io, csv
    from fastapi.responses import StreamingResponse
    output = io.StringIO()
    fieldnames = [
        "position", "mark", "type_name", "quantity",
        "length_x", "width_y", "height_z",
        "unit_weight_kg", "total_weight_kg",
        "unit_area_m2", "total_area_m2", "ptm",
        "ogz_notes", "steel_grade", "profile_type",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in data["items"]:
        writer.writerow(item)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=parse_result.csv"},
    )


@router.get("/batches/{batch_id}/export/xlsx")
async def export_batch_xlsx(batch_id: str, db: AsyncSession = Depends(get_db)):
    data = await get_batch_from_db(db, batch_id)
    if not data:
        raise HTTPException(404, "Пакет не найден")
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    df = pd.DataFrame(data["items"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ведомость марок")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=parse_result.xlsx"},
    )
