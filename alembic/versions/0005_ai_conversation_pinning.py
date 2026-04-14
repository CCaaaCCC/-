"""add ai conversation pinning fields

Revision ID: 0005_ai_conversation_pinning
Revises: 0004_ai_conversation_history
Create Date: 2026-04-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0005_ai_conversation_pinning"
down_revision = "0004_ai_conversation_history"
branch_labels = None
depends_on = None


def _safe_indexes(inspector, table_name: str) -> set[str]:
    try:
        return {idx["name"] for idx in inspector.get_indexes(table_name)}
    except Exception:
        return set()


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
    if "is_pinned" not in columns:
        op.add_column(
            "ai_conversations",
            sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("ai_conversations", "is_pinned", server_default=None)

    if "pinned_at" not in columns:
        op.add_column("ai_conversations", sa.Column("pinned_at", sa.DateTime(), nullable=True))

    inspector = inspect(bind)
    indexes = _safe_indexes(inspector, "ai_conversations")
    if op.f("ix_ai_conversations_is_pinned") not in indexes:
        op.create_index(op.f("ix_ai_conversations_is_pinned"), "ai_conversations", ["is_pinned"], unique=False)
    if op.f("ix_ai_conversations_pinned_at") not in indexes:
        op.create_index(op.f("ix_ai_conversations_pinned_at"), "ai_conversations", ["pinned_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "ai_conversations" not in tables:
        return

    indexes = _safe_indexes(inspector, "ai_conversations")
    if op.f("ix_ai_conversations_pinned_at") in indexes:
        op.drop_index(op.f("ix_ai_conversations_pinned_at"), table_name="ai_conversations")
    if op.f("ix_ai_conversations_is_pinned") in indexes:
        op.drop_index(op.f("ix_ai_conversations_is_pinned"), table_name="ai_conversations")

    inspector = inspect(bind)
    columns = _safe_columns(inspector, "ai_conversations")
    if "pinned_at" in columns:
        op.drop_column("ai_conversations", "pinned_at")
    if "is_pinned" in columns:
        op.drop_column("ai_conversations", "is_pinned")
