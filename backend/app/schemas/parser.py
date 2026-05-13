from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class LineItemSchema(BaseModel):
    position: Optional[int] = None
    mark: Optional[str] = None
    type_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    length_x: Optional[Decimal] = None
    width_y: Optional[Decimal] = None
    height_z: Optional[Decimal] = None
    unit_weight_kg: Optional[Decimal] = None
    total_weight_kg: Optional[Decimal] = None
    unit_area_m2: Optional[Decimal] = None
    total_area_m2: Optional[Decimal] = None
    ogz_notes: Optional[str] = None
    profile_type: Optional[str] = None
    steel_grade: Optional[str] = None
    gost_code: Optional[str] = None
    confidence: float = 1.0
    issues: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UnrecognizedRowSchema(BaseModel):
    raw_text: Optional[str] = None
    partial_data: dict = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)


class MetadataSchema(BaseModel):
    project_code: Optional[str] = None
    object_name: Optional[str] = None
    stage: Optional[str] = None


class ParseResultSchema(BaseModel):
    source_file: str
    batch_type: str
    metadata: MetadataSchema = Field(default_factory=MetadataSchema)
    items: list[LineItemSchema] = Field(default_factory=list)
    unrecognized_rows: list[UnrecognizedRowSchema] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_rows_parsed: int = 0
    total_rows_raw: int = 0
    success_rate: float = 0.0


class BatchPreviewSchema(BaseModel):
    batch_id: UUID
    source_file: str
    status: str
    total_items: int
    items: list[LineItemSchema] = Field(default_factory=list)
    unrecognized_count: int = 0


class ProjectCreateSchema(BaseModel):
    external_code: Optional[str] = None
    name: Optional[str] = None
    stage: Optional[str] = None


class ProjectSchema(BaseModel):
    id: UUID
    external_code: Optional[str] = None
    name: Optional[str] = None
    stage: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
