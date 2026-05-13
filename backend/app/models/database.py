import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Numeric, Text, DateTime,
    ForeignKey, Enum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class BatchStatus(str, PyEnum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    VERIFIED = "verified"
    ERROR = "error"


class BatchType(str, PyEnum):
    KMD = "kmd"
    VOR = "vor"
    SPEC = "spec"
    GENERAL = "general"


class ItemStatus(str, PyEnum):
    RAW = "raw"
    VERIFIED = "verified"
    REJECTED = "rejected"


class OfferStatus(str, PyEnum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SIGNED = "signed"


class IncomingStatus(str, PyEnum):
    PENDING = "pending"
    MATCHED = "matched"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_code: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batches: Mapped[list["DocumentBatch"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    line_items: Mapped[list["LineItem"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    commercial_offers: Mapped[list["CommercialOffer"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    client: Mapped["Client | None"] = relationship(back_populates="projects")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    inn: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    contacts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="client")


class DocumentBatch(Base):
    __tablename__ = "document_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    batch_type: Mapped[BatchType] = mapped_column(Enum(BatchType), nullable=False, default=BatchType.KMD)
    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.UPLOADED)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="batches")
    line_items: Mapped[list["LineItem"]] = relationship(back_populates="batch", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("document_batches.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    source_sheet: Mapped[str] = mapped_column(String(100), nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mark: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    type_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    length_x: Mapped[Decimal | None] = mapped_column(Numeric(10, 1), nullable=True)
    width_y: Mapped[Decimal | None] = mapped_column(Numeric(10, 1), nullable=True)
    height_z: Mapped[Decimal | None] = mapped_column(Numeric(10, 1), nullable=True)
    unit_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    total_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ptm: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    ogz_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    steel_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gost_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.RAW)
    parse_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    batch: Mapped["DocumentBatch"] = relationship(back_populates="line_items")
    project: Mapped[Project | None] = relationship(back_populates="line_items")


class SteelProfile(Base):
    __tablename__ = "steel_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    gost_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    steel_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    section_type: Mapped[str | None] = mapped_column(String(50), nullable=True)


class OgzComposition(Base):
    __tablename__ = "ogz_compositions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    composition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    consumption_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    price_per_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    dry_residue: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    density: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    min_ptm_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_ptm_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    rei_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    environment: Mapped[str | None] = mapped_column(String(30), nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class CommercialOffer(Base):
    __tablename__ = "commercial_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    total_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    material_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    work_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus), default=OfferStatus.DRAFT)

    project: Mapped["Project"] = relationship(back_populates="commercial_offers")


class IncomingRequest(Base):
    __tablename__ = "incoming_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    sender_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    sender_name: Mapped[str] = mapped_column(String(500), nullable=True)
    subject: Mapped[str] = mapped_column(String(1000), nullable=True)
    body_preview: Mapped[str] = mapped_column(Text, nullable=True)
    attachments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[IncomingStatus] = mapped_column(Enum(IncomingStatus), default=IncomingStatus.PENDING)
    matched_by: Mapped[str] = mapped_column(String(50), nullable=True)
    result_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client: Mapped["Client | None"] = relationship(foreign_keys=[client_id])
    project: Mapped["Project | None"] = relationship(foreign_keys=[project_id])


class EmployeeRole(str, PyEnum):
    CHIEF_ENGINEER = "chief_engineer"
    SHOP_MASTER = "shop_master"
    WORKER = "worker"
    MANAGER = "manager"
    SUPPLY = "supply"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    role: Mapped[EmployeeRole] = mapped_column(Enum(EmployeeRole), default=EmployeeRole.WORKER)
    department: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_WORK = "in_work"
    DONE = "done"
    QUESTION = "question"
    REJECTED = "rejected"


class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    line_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("line_items.id"), nullable=True)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    mark: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    drawing_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    telegram_msg_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    project: Mapped["Project | None"] = relationship(foreign_keys=[project_id])
    line_item: Mapped["LineItem | None"] = relationship(foreign_keys=[line_item_id])
    employee: Mapped["Employee"] = relationship(foreign_keys=[assigned_to])
    creator: Mapped["Employee | None"] = relationship(foreign_keys=[assigned_by])
