"""Create initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("inn", sa.String(20), nullable=True),
        sa.Column("contacts", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("external_code", sa.String(255), nullable=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "steel_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_name", sa.String(100), nullable=False),
        sa.Column("gost_code", sa.String(50), nullable=True),
        sa.Column("steel_grade", sa.String(20), nullable=True),
        sa.Column("unit_weight_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("section_type", sa.String(50), nullable=True),
    )
    op.create_table(
        "ogz_compositions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("composition_type", sa.String(50), nullable=False),
        sa.Column("consumption_rate", sa.Numeric(10, 4), nullable=True),
        sa.Column("price_per_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("supplier_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_table(
        "document_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("batch_type", sa.String(20), nullable=False),
        sa.Column("source_file", sa.String(500), nullable=False),
        sa.Column("page_count", sa.Integer(), default=0),
        sa.Column("status", sa.String(20), default="uploaded"),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("parsed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", UUID(as_uuid=True), sa.ForeignKey("document_batches.id"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("source_sheet", sa.String(100), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("mark", sa.String(100), nullable=True),
        sa.Column("type_name", sa.String(200), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=True),
        sa.Column("length_x", sa.Numeric(10, 1), nullable=True),
        sa.Column("width_y", sa.Numeric(10, 1), nullable=True),
        sa.Column("height_z", sa.Numeric(10, 1), nullable=True),
        sa.Column("unit_weight_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_weight_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("unit_area_m2", sa.Numeric(10, 4), nullable=True),
        sa.Column("total_area_m2", sa.Numeric(12, 4), nullable=True),
        sa.Column("ogz_notes", sa.Text(), nullable=True),
        sa.Column("profile_type", sa.String(50), nullable=True),
        sa.Column("steel_grade", sa.String(20), nullable=True),
        sa.Column("gost_code", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), default="raw"),
        sa.Column("parse_confidence", sa.Float(), default=1.0),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "commercial_offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.Column("total_area_m2", sa.Numeric(12, 4), nullable=True),
        sa.Column("total_weight_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("material_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("work_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(20), default="draft"),
    )
    op.create_index("ix_projects_external_code", "projects", ["external_code"])
    op.create_index("ix_line_items_mark", "line_items", ["mark"])
    op.create_index("ix_steel_profiles_profile_name", "steel_profiles", ["profile_name"])


def downgrade() -> None:
    op.drop_table("commercial_offers")
    op.drop_table("line_items")
    op.drop_table("document_batches")
    op.drop_table("ogz_compositions")
    op.drop_table("steel_profiles")
    op.drop_table("projects")
    op.drop_table("clients")
