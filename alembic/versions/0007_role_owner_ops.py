"""add ownership fields for plants and groups

Revision ID: 0007_role_owner
Revises: 0006_pin_default
Create Date: 2026-04-12

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0007_role_owner"
down_revision = "0006_pin_default"
branch_labels = None
depends_on = None


def _safe_columns(inspector, table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspector.get_columns(table_name)}
    except Exception:
        return set()


def _safe_indexes(inspector, table_name: str) -> set[str]:
    try:
        return {idx["name"] for idx in inspector.get_indexes(table_name)}
    except Exception:
        return set()


def _safe_fk_columns(inspector, table_name: str) -> set[str]:
    try:
        cols: set[str] = set()
        for fk in inspector.get_foreign_keys(table_name):
            for col in fk.get("constrained_columns") or []:
                cols.add(col)
        return cols
    except Exception:
        return set()


def _ensure_owner_column(table_name: str, index_name: str, fk_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if table_name not in tables:
        return

    columns = _safe_columns(inspector, table_name)
    if "created_by" not in columns:
        op.add_column(table_name, sa.Column("created_by", sa.Integer(), nullable=True))

    inspector = inspect(bind)
    columns = _safe_columns(inspector, table_name)
    indexes = _safe_indexes(inspector, table_name)
    if "created_by" in columns and index_name not in indexes:
        op.create_index(index_name, table_name, ["created_by"], unique=False)

    fk_columns = _safe_fk_columns(inspector, table_name)
    if "created_by" in columns and "created_by" not in fk_columns:
        op.create_foreign_key(fk_name, table_name, "users", ["created_by"], ["id"])


def _drop_owner_column(table_name: str, index_name: str, fk_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if table_name not in tables:
        return

    columns = _safe_columns(inspector, table_name)
    if "created_by" not in columns:
        return

    indexes = _safe_indexes(inspector, table_name)
    if index_name in indexes:
        op.drop_index(index_name, table_name=table_name)

    try:
        op.drop_constraint(fk_name, table_name, type_="foreignkey")
    except Exception:
        pass

    op.drop_column(table_name, "created_by")


def upgrade() -> None:
    _ensure_owner_column(
        table_name="plant_profiles",
        index_name="ix_plant_profiles_created_by",
        fk_name="fk_plant_profiles_created_by_users",
    )
    _ensure_owner_column(
        table_name="study_groups",
        index_name="ix_study_groups_created_by",
        fk_name="fk_study_groups_created_by_users",
    )


def downgrade() -> None:
    _drop_owner_column(
        table_name="study_groups",
        index_name="ix_study_groups_created_by",
        fk_name="fk_study_groups_created_by_users",
    )
    _drop_owner_column(
        table_name="plant_profiles",
        index_name="ix_plant_profiles_created_by",
        fk_name="fk_plant_profiles_created_by_users",
    )
