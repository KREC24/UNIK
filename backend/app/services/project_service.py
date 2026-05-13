from typing import Optional
from app.schemas.parser import ParseResultSchema


_in_memory_batches: dict[str, ParseResultSchema] = {}


def store_batch(batch_id: str, result: ParseResultSchema):
    _in_memory_batches[batch_id] = result


def get_batch(batch_id: str) -> Optional[ParseResultSchema]:
    return _in_memory_batches.get(batch_id)


def get_batches_for_project(project_id: str) -> list[dict]:
    return [
        {
            "batch_id": bid,
            "source_file": r.source_file,
            "total_items": len(r.items),
            "success_rate": r.success_rate,
        }
        for bid, r in _in_memory_batches.items()
    ]
