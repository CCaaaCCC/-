"""set ai conversation pinning server default

Revision ID: 0006_pin_default
Revises: 0005_ai_conversation_pinning
Create Date: 2026-04-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0006_pin_default"
down_revision = "0005_ai_conversation_pinning"
branch_labels = None
depends_on = None


def _safe_columns(inspector, table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspector.get_columns(table_name)}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "ai_conversations" not in tables:
        return

    columns = _safe_columns(inspector, "ai_conversations")
    if "is_pinned" in columns:
        op.alter_column(
            "ai_conversations",
            "is_pinned",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "ai_conversations" not in tables:
        return

    columns = _safe_columns(inspector, "ai_conversations")
    if "is_pinned" in columns:
        op.alter_column(
            "ai_conversations",
            "is_pinned",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=None,
        )
