"""add market module, invite code and content tags

Revision ID: 0008_market_tags
Revises: 0007_role_owner
Create Date: 2026-04-17

"""

from __future__ import annotations

import random

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0008_market_tags"
down_revision = "0007_role_owner"
branch_labels = None
depends_on = None


INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _columns(inspector, table_name: str) -> set[str]:
    try:
        return {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        return set()


def _indexes(inspector, table_name: str) -> set[str]:
    try:
        return {idx["name"] for idx in inspector.get_indexes(table_name)}
    except Exception:
        return set()


def _generate_invite_code(existing: set[str]) -> str:
    while True:
        code = "".join(random.choice(INVITE_CODE_ALPHABET) for _ in range(8))
        if code not in existing:
            existing.add(code)
            return code


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, "classes"):
        class_cols = _columns(inspector, "classes")
        if "invite_code" not in class_cols:
            op.add_column("classes", sa.Column("invite_code", sa.String(length=32), nullable=True))

        inspector = inspect(bind)
        class_indexes = _indexes(inspector, "classes")
        if "ix_classes_invite_code" not in class_indexes:
            op.create_index("ix_classes_invite_code", "classes", ["invite_code"], unique=True)

        rows = bind.execute(sa.text("SELECT id, invite_code FROM classes")).fetchall()
        existing_codes = {row.invite_code for row in rows if row.invite_code}
        for row in rows:
            if not row.invite_code:
                new_code = _generate_invite_code(existing_codes)
                bind.execute(
                    sa.text("UPDATE classes SET invite_code = :code WHERE id = :id"),
                    {"code": new_code, "id": row.id},
                )

        op.alter_column(
            "classes",
            "invite_code",
            existing_type=sa.String(length=32),
            nullable=False,
        )

    inspector = inspect(bind)
    if _table_exists(inspector, "teaching_contents"):
        content_cols = _columns(inspector, "teaching_contents")

        if "tags" not in content_cols:
            op.add_column("teaching_contents", sa.Column("tags", sa.String(length=500), nullable=True))

        content_indexes = _indexes(inspector, "teaching_contents")
        if "ix_teaching_contents_tags" not in content_indexes:
            op.create_index("ix_teaching_contents_tags", "teaching_contents", ["tags"], unique=False)

        if "category_id" in content_cols:
            for fk in inspector.get_foreign_keys("teaching_contents"):
                fk_name = fk.get("name")
                constrained = fk.get("constrained_columns") or []
                if fk_name and "category_id" in constrained:
                    try:
                        op.drop_constraint(fk_name, "teaching_contents", type_="foreignkey")
                    except Exception:
                        pass

            content_indexes = _indexes(inspector, "teaching_contents")
            if "ix_teaching_contents_category_id" in content_indexes:
                op.drop_index("ix_teaching_contents_category_id", table_name="teaching_contents")

            op.drop_column("teaching_contents", "category_id")

    inspector = inspect(bind)
    if _table_exists(inspector, "content_categories"):
        op.drop_table("content_categories")

    inspector = inspect(bind)
    if not _table_exists(inspector, "market_products"):
        op.create_table(
            "market_products",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.DECIMAL(10, 2), nullable=True),
            sa.Column("location", sa.String(length=255), nullable=False),
            sa.Column("contact_info", sa.String(length=255), nullable=False),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("seller_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("view_count", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            mysql_charset="utf8mb4",
            mysql_engine="InnoDB",
        )
        op.create_index("ix_market_products_id", "market_products", ["id"], unique=False)
        op.create_index("ix_market_products_title", "market_products", ["title"], unique=False)
        op.create_index("ix_market_products_seller_id", "market_products", ["seller_id"], unique=False)
        op.create_index("ix_market_products_status", "market_products", ["status"], unique=False)
        op.create_index("ix_market_products_created_at", "market_products", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, "market_products"):
        indexes = _indexes(inspector, "market_products")
        for index_name in [
            "ix_market_products_created_at",
            "ix_market_products_status",
            "ix_market_products_seller_id",
            "ix_market_products_title",
            "ix_market_products_id",
        ]:
            if index_name in indexes:
                op.drop_index(index_name, table_name="market_products")
        op.drop_table("market_products")

    inspector = inspect(bind)
    if _table_exists(inspector, "content_categories") is False:
        op.create_table(
            "content_categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["parent_id"], ["content_categories.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_content_categories_id", "content_categories", ["id"], unique=False)

    inspector = inspect(bind)
    if _table_exists(inspector, "teaching_contents"):
        content_cols = _columns(inspector, "teaching_contents")
        content_indexes = _indexes(inspector, "teaching_contents")

        if "category_id" not in content_cols:
            op.add_column("teaching_contents", sa.Column("category_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                "fk_teaching_contents_category_id_content_categories",
                "teaching_contents",
                "content_categories",
                ["category_id"],
                ["id"],
            )
            if "ix_teaching_contents_category_id" not in content_indexes:
                op.create_index("ix_teaching_contents_category_id", "teaching_contents", ["category_id"], unique=False)

        if "tags" in content_cols:
            if "ix_teaching_contents_tags" in content_indexes:
                op.drop_index("ix_teaching_contents_tags", table_name="teaching_contents")
            op.drop_column("teaching_contents", "tags")

    inspector = inspect(bind)
    if _table_exists(inspector, "classes"):
        class_cols = _columns(inspector, "classes")
        class_indexes = _indexes(inspector, "classes")
        if "invite_code" in class_cols:
            if "ix_classes_invite_code" in class_indexes:
                op.drop_index("ix_classes_invite_code", table_name="classes")
            op.drop_column("classes", "invite_code")
