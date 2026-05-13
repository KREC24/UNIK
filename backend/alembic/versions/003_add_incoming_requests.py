"""add incoming_requests and client email

Revision ID: 003
Revises: 002_add_ptm_and_composition_fields
Create Date: 2026-05-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002_add_ptm_and_composition_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("email", sa.String(255), nullable=True))
    op.create_index("ix_clients_email", "clients", ["email"])

    op.create_table(
        "incoming_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("sender_email", sa.String(320), nullable=False),
        sa.Column("sender_name", sa.String(500), nullable=True),
        sa.Column("subject", sa.String(1000), nullable=True),
        sa.Column("body_preview", sa.Text, nullable=True),
        sa.Column("attachments", sa.JSON, nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "matched", "processing", "processed", "failed", name="incomingstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("matched_by", sa.String(50), nullable=True),
        sa.Column("result_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("received_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incoming_requests_sender_email", "incoming_requests", ["sender_email"])
    op.create_index("ix_incoming_requests_received_at", "incoming_requests", ["received_at"])


def downgrade() -> None:
    op.drop_table("incoming_requests")
    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_column("clients", "email")
    sa.Enum(name="incomingstatus").drop(op.get_bind(), checkfirst=True)
