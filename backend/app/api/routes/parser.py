import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.parser import ParseResultSchema
from app.services.parsing_service import (
    parse_shipping_list, parse_general_data, auto_detect_and_parse,
)
from app.services.export_service import export_json, export_csv, export_xlsx

router = APIRouter(prefix="/parse", tags=["Parser"])

_in_memory_results: dict[str, ParseResultSchema] = {}


@router.post("/upload", response_model=ParseResultSchema)
async def upload_pdf(
    file: UploadFile = File(...),
    parser_type: Optional[str] = Query(None, description="shipping | general | auto"),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Принимаются только PDF-файлы")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = settings.UPLOAD_DIR / safe_name

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"Файл превышает {settings.MAX_UPLOAD_SIZE_MB} МБ")

    file_path.write_bytes(content)

    try:
        if parser_type == "shipping":
            result = parse_shipping_list(file_path)
        elif parser_type == "general":
            result = parse_general_data(file_path)
        else:
            result = auto_detect_and_parse(file_path)
    except Exception as e:
        raise HTTPException(500, f"Ошибка парсинга: {e}")

    batch_id = uuid.uuid4().hex
    _in_memory_results[batch_id] = result

    return JSONResponse(
        content={
            **result.model_dump(),
            "batch_id": batch_id,
        },
    )


@router.get("/batches/{batch_id}", response_model=ParseResultSchema)
async def get_batch_status(batch_id: str):
    result = _in_memory_results.get(batch_id)
    if not result:
        raise HTTPException(404, "Пакет не найден")
    return JSONResponse(content=result.model_dump())


@router.get("/batches/{batch_id}/preview")
async def preview_batch(batch_id: str):
    result = _in_memory_results.get(batch_id)
    if not result:
        raise HTTPException(404, "Пакет не найден")
    return JSONResponse(content={
        "batch_id": batch_id,
        "source_file": result.source_file,
        "status": "parsed",
        "total_items": len(result.items),
        "items": [item.model_dump() for item in result.items[:100]],
        "unrecognized_count": len(result.unrecognized_rows),
    })


@router.get("/batches/{batch_id}/export/json")
async def export_batch_json(batch_id: str):
    result = _in_memory_results.get(batch_id)
    if not result:
        raise HTTPException(404, "Пакет не найден")
    return export_json(result)


@router.get("/batches/{batch_id}/export/csv")
async def export_batch_csv(batch_id: str):
    result = _in_memory_results.get(batch_id)
    if not result:
        raise HTTPException(404, "Пакет не найден")
    return export_csv(result)


@router.get("/batches/{batch_id}/export/xlsx")
async def export_batch_xlsx(batch_id: str):
    result = _in_memory_results.get(batch_id)
    if not result:
        raise HTTPException(404, "Пакет не найден")
    return export_xlsx(result)
