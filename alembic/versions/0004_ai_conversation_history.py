"""add ai conversation and message tables

Revision ID: 0004_ai_conversation_history
Revises: 0003_profile_notify
Create Date: 2026-04-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_ai_conversation_history"
down_revision = "0003_profile_notify"
branch_labels = None
depends_on = None


def _safe_indexes(inspector, table_name: str) -> set[str]:
    try:
        return {idx["name"] for idx in inspector.get_indexes(table_name)}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "ai_conversations" not in tables:
        op.create_table(
            "ai_conversations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("last_message_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            mysql_charset="utf8mb4",
            mysql_engine="InnoDB",
        )
        op.create_index(op.f("ix_ai_conversations_id"), "ai_conversations", ["id"], unique=False)

    conv_indexes = _safe_indexes(inspector, "ai_conversations")
    if op.f("ix_ai_conversations_user_id") not in conv_indexes:
        op.create_index(op.f("ix_ai_conversations_user_id"), "ai_conversations", ["user_id"], unique=False)
    if op.f("ix_ai_conversations_created_at") not in conv_indexes:
        op.create_index(op.f("ix_ai_conversations_created_at"), "ai_conversations", ["created_at"], unique=False)
    if op.f("ix_ai_conversations_updated_at") not in conv_indexes:
        op.create_index(op.f("ix_ai_conversations_updated_at"), "ai_conversations", ["updated_at"], unique=False)
    if op.f("ix_ai_conversations_last_message_at") not in conv_indexes:
        op.create_index(op.f("ix_ai_conversations_last_message_at"), "ai_conversations", ["last_message_at"], unique=False)

    # refresh inspector after possible table creation
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "ai_conversation_messages" not in tables:
        op.create_table(
            "ai_conversation_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("conversation_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("reasoning", sa.Text(), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("model", sa.String(length=80), nullable=True),
            sa.Column("citations_json", sa.Text(), nullable=True),
            sa.Column("web_search_notice", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"]),
            sa.PrimaryKeyConstraint("id"),
            mysql_charset="utf8mb4",
            mysql_engine="InnoDB",
        )
        op.create_index(op.f("ix_ai_conversation_messages_id"), "ai_conversation_messages", ["id"], unique=False)

    msg_indexes = _safe_indexes(inspector, "ai_conversation_messages")
    if op.f("ix_ai_conversation_messages_conversation_id") not in msg_indexes:
        op.create_index(
            op.f("ix_ai_conversation_messages_conversation_id"),
            "ai_conversation_messages",
            ["conversation_id"],
            unique=False,
        )
    if op.f("ix_ai_conversation_messages_role") not in msg_indexes:
        op.create_index(op.f("ix_ai_conversation_messages_role"), "ai_conversation_messages", ["role"], unique=False)
    if op.f("ix_ai_conversation_messages_created_at") not in msg_indexes:
        op.create_index(
            op.f("ix_ai_conversation_messages_created_at"),
            "ai_conversation_messages",
            ["created_at"],
            unique=False,
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "ai_conversation_messages" in tables:
        msg_indexes = _safe_indexes(inspector, "ai_conversation_messages")
        if op.f("ix_ai_conversation_messages_created_at") in msg_indexes:
            op.drop_index(op.f("ix_ai_conversation_messages_created_at"), table_name="ai_conversation_messages")
        if op.f("ix_ai_conversation_messages_role") in msg_indexes:
            op.drop_index(op.f("ix_ai_conversation_messages_role"), table_name="ai_conversation_messages")
        if op.f("ix_ai_conversation_messages_conversation_id") in msg_indexes:
            op.drop_index(op.f("ix_ai_conversation_messages_conversation_id"), table_name="ai_conversation_messages")
        if op.f("ix_ai_conversation_messages_id") in msg_indexes:
            op.drop_index(op.f("ix_ai_conversation_messages_id"), table_name="ai_conversation_messages")
        op.drop_table("ai_conversation_messages")

    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "ai_conversations" in tables:
        conv_indexes = _safe_indexes(inspector, "ai_conversations")
        if op.f("ix_ai_conversations_last_message_at") in conv_indexes:
            op.drop_index(op.f("ix_ai_conversations_last_message_at"), table_name="ai_conversations")
        if op.f("ix_ai_conversations_updated_at") in conv_indexes:
            op.drop_index(op.f("ix_ai_conversations_updated_at"), table_name="ai_conversations")
        if op.f("ix_ai_conversations_created_at") in conv_indexes:
            op.drop_index(op.f("ix_ai_conversations_created_at"), table_name="ai_conversations")
        if op.f("ix_ai_conversations_user_id") in conv_indexes:
            op.drop_index(op.f("ix_ai_conversations_user_id"), table_name="ai_conversations")
        if op.f("ix_ai_conversations_id") in conv_indexes:
            op.drop_index(op.f("ix_ai_conversations_id"), table_name="ai_conversations")
        op.drop_table("ai_conversations")
