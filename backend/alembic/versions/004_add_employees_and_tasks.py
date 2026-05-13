"""add employees and task_assignments

Revision ID: 004
Revises: 003_add_incoming_requests
Create Date: 2026-05-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003_add_incoming_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(300), nullable=False),
        sa.Column("telegram_id", sa.String(100), nullable=True),
        sa.Column(
            "role",
            sa.Enum("chief_engineer", "shop_master", "worker", "manager", "supply", name="employeerole"),
            nullable=False,
            server_default="worker",
        ),
        sa.Column("department", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_employees_telegram_id", "employees", ["telegram_id"])

    op.create_table(
        "task_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("line_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("line_items.id"), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("mark", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("total_weight_kg", sa.Numeric(12, 2), nullable=True),
        sa.Column("drawing_url", sa.String(1000), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "in_work", "done", "question", "rejected", name="taskstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("deadline", sa.DateTime, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("telegram_msg_id", sa.String(100), nullable=True),
        sa.Column("status_changed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_task_assignments_created_at", "task_assignments", ["created_at"])


def downgrade() -> None:
    op.drop_table("task_assignments")
    op.drop_table("employees")
    sa.Enum(name="taskstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="employeerole").drop(op.get_bind(), checkfirst=True)
