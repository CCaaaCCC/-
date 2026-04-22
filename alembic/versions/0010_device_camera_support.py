"""add has_camera to devices

Revision ID: 0010_device_camera_support
Revises: 0009_device_actuator_levels
Create Date: 2026-04-21

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0010_device_camera_support"
down_revision = "0009_device_actuator_levels"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _columns(inspector, table_name: str) -> set[str]:
    try:
        return {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, "devices"):
        return

    device_cols = _columns(inspector, "devices")

    if "has_camera" not in device_cols:
        op.add_column(
            "devices",
            sa.Column("has_camera", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, "devices"):
        return

    device_cols = _columns(inspector, "devices")

    if "has_camera" in device_cols:
        op.drop_column("devices", "has_camera")
