"""add profile avatar, threaded comments, likes and notifications

Revision ID: 0003_profile_notify
Revises: 0002_sub_files
Create Date: 2026-04-01

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0003_profile_notify"
down_revision = "0002_sub_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "avatar_url" not in user_columns:
        op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))

    comment_columns = {col["name"] for col in inspector.get_columns("content_comments")}
    if "parent_id" not in comment_columns:
        op.add_column("content_comments", sa.Column("parent_id", sa.Integer(), nullable=True))
    if "like_count" not in comment_columns:
        op.add_column("content_comments", sa.Column("like_count", sa.Integer(), nullable=True))

    comment_indexes = {idx["name"] for idx in inspector.get_indexes("content_comments")}
    if op.f("ix_content_comments_parent_id") not in comment_indexes:
        op.create_index(op.f("ix_content_comments_parent_id"), "content_comments", ["parent_id"], unique=False)

    comment_fks = {fk["name"] for fk in inspector.get_foreign_keys("content_comments")}
    if "fk_content_comments_parent_id" not in comment_fks:
        op.create_foreign_key(
            "fk_content_comments_parent_id",
            "content_comments",
            "content_comments",
            ["parent_id"],
            ["id"],
        )

    tables = set(inspector.get_table_names())

    if "content_comment_likes" not in tables:
        op.create_table(
            "content_comment_likes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("comment_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["comment_id"], ["content_comments.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("comment_id", "user_id", name="uix_comment_like_user"),
            mysql_charset="utf8mb4",
            mysql_engine="InnoDB",
        )
        op.create_index(op.f("ix_content_comment_likes_id"), "content_comment_likes", ["id"], unique=False)
        op.create_index(op.f("ix_content_comment_likes_comment_id"), "content_comment_likes", ["comment_id"], unique=False)
        op.create_index(op.f("ix_content_comment_likes_user_id"), "content_comment_likes", ["user_id"], unique=False)
        op.create_index(op.f("ix_content_comment_likes_created_at"), "content_comment_likes", ["created_at"], unique=False)

    if "user_notifications" not in tables:
        op.create_table(
            "user_notifications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("notification_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("content_id", sa.Integer(), nullable=True),
            sa.Column("comment_id", sa.Integer(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["comment_id"], ["content_comments.id"]),
            sa.ForeignKeyConstraint(["content_id"], ["teaching_contents.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_user_notifications_id"), "user_notifications", ["id"], unique=False)
        op.create_index(op.f("ix_user_notifications_user_id"), "user_notifications", ["user_id"], unique=False)
        op.create_index(op.f("ix_user_notifications_actor_id"), "user_notifications", ["actor_id"], unique=False)
        op.create_index(op.f("ix_user_notifications_notification_type"), "user_notifications", ["notification_type"], unique=False)
        op.create_index(op.f("ix_user_notifications_content_id"), "user_notifications", ["content_id"], unique=False)
        op.create_index(op.f("ix_user_notifications_comment_id"), "user_notifications", ["comment_id"], unique=False)
        op.create_index(op.f("ix_user_notifications_is_read"), "user_notifications", ["is_read"], unique=False)
        op.create_index(op.f("ix_user_notifications_created_at"), "user_notifications", ["created_at"], unique=False)


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "user_notifications" in tables:
        op.drop_index(op.f("ix_user_notifications_created_at"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_is_read"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_comment_id"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_content_id"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_notification_type"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_actor_id"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_user_id"), table_name="user_notifications")
        op.drop_index(op.f("ix_user_notifications_id"), table_name="user_notifications")
        op.drop_table("user_notifications")

    if "content_comment_likes" in tables:
        op.drop_index(op.f("ix_content_comment_likes_created_at"), table_name="content_comment_likes")
        op.drop_index(op.f("ix_content_comment_likes_user_id"), table_name="content_comment_likes")
        op.drop_index(op.f("ix_content_comment_likes_comment_id"), table_name="content_comment_likes")
        op.drop_index(op.f("ix_content_comment_likes_id"), table_name="content_comment_likes")
        op.drop_table("content_comment_likes")

    comment_columns = {col["name"] for col in inspector.get_columns("content_comments")}
    if "parent_id" in comment_columns:
        comment_fks = {fk["name"] for fk in inspector.get_foreign_keys("content_comments")}
        if "fk_content_comments_parent_id" in comment_fks:
            op.drop_constraint("fk_content_comments_parent_id", "content_comments", type_="foreignkey")
        comment_indexes = {idx["name"] for idx in inspector.get_indexes("content_comments")}
        if op.f("ix_content_comments_parent_id") in comment_indexes:
            op.drop_index(op.f("ix_content_comments_parent_id"), table_name="content_comments")
        op.drop_column("content_comments", "parent_id")
    if "like_count" in comment_columns:
        op.drop_column("content_comments", "like_count")

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "avatar_url" in user_columns:
        op.drop_column("users", "avatar_url")
