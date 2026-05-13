"""Add ptm, composition fields, offer version

Revision ID: 002
Revises: 001
Create Date: 2026-05-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("line_items", sa.Column("ptm", sa.Numeric(10, 4), nullable=True))

    op.add_column("ogz_compositions", sa.Column("dry_residue", sa.Numeric(5, 1), nullable=True))
    op.add_column("ogz_compositions", sa.Column("density", sa.Numeric(5, 2), nullable=True))
    op.add_column("ogz_compositions", sa.Column("min_ptm_mm", sa.Numeric(8, 4), nullable=True))
    op.add_column("ogz_compositions", sa.Column("max_ptm_mm", sa.Numeric(8, 4), nullable=True))
    op.add_column("ogz_compositions", sa.Column("rei_minutes", sa.Integer(), nullable=True))
    op.add_column("ogz_compositions", sa.Column("environment", sa.String(30), nullable=True))

    op.add_column("commercial_offers", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("line_items", "ptm")

    op.drop_column("ogz_compositions", "dry_residue")
    op.drop_column("ogz_compositions", "density")
    op.drop_column("ogz_compositions", "min_ptm_mm")
    op.drop_column("ogz_compositions", "max_ptm_mm")
    op.drop_column("ogz_compositions", "rei_minutes")
    op.drop_column("ogz_compositions", "environment")

    op.drop_column("commercial_offers", "version")
