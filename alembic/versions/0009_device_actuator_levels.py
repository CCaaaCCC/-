"""add fan speed and light brightness to devices

Revision ID: 0009_device_actuator_levels
Revises: 0008_market_tags
Create Date: 2026-04-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0009_device_actuator_levels"
down_revision = "0008_market_tags"
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

    if "fan_speed" not in device_cols:
        op.add_column(
            "devices",
            sa.Column("fan_speed", sa.SmallInteger(), nullable=False, server_default="100"),
        )

    if "light_brightness" not in device_cols:
        op.add_column(
            "devices",
            sa.Column("light_brightness", sa.SmallInteger(), nullable=False, server_default="100"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, "devices"):
        return

    device_cols = _columns(inspector, "devices")

    if "light_brightness" in device_cols:
        op.drop_column("devices", "light_brightness")

    if "fan_speed" in device_cols:
        op.drop_column("devices", "fan_speed")
