"""add submission grading and report file fields

Revision ID: 0002_assignment_submission_file_fields
Revises: 0001_init_schema
Create Date: 2026-03-27

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002_sub_files"
down_revision = "0001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("assignment_submissions")}

    if "submitted_at" not in columns:
        op.add_column("assignment_submissions", sa.Column("submitted_at", sa.DateTime(), nullable=True))
    if "graded_at" not in columns:
        op.add_column("assignment_submissions", sa.Column("graded_at", sa.DateTime(), nullable=True))
    if "graded_by" not in columns:
        op.add_column("assignment_submissions", sa.Column("graded_by", sa.Integer(), nullable=True))
    if "report_file_name" not in columns:
        op.add_column("assignment_submissions", sa.Column("report_file_name", sa.String(length=255), nullable=True))
    if "report_file_path" not in columns:
        op.add_column("assignment_submissions", sa.Column("report_file_path", sa.String(length=500), nullable=True))
    if "report_file_size" not in columns:
        op.add_column("assignment_submissions", sa.Column("report_file_size", sa.Integer(), nullable=True))

    indexes = {idx["name"] for idx in inspector.get_indexes("assignment_submissions")}
    if op.f("ix_assignment_submissions_submitted_at") not in indexes:
        op.create_index(op.f("ix_assignment_submissions_submitted_at"), "assignment_submissions", ["submitted_at"], unique=False)
    if op.f("ix_assignment_submissions_graded_at") not in indexes:
        op.create_index(op.f("ix_assignment_submissions_graded_at"), "assignment_submissions", ["graded_at"], unique=False)
    if op.f("ix_assignment_submissions_graded_by") not in indexes:
        op.create_index(op.f("ix_assignment_submissions_graded_by"), "assignment_submissions", ["graded_by"], unique=False)

    fks = {fk["name"] for fk in inspector.get_foreign_keys("assignment_submissions")}
    if "fk_assignment_submissions_graded_by_users" not in fks:
        op.create_foreign_key(
            "fk_assignment_submissions_graded_by_users",
            "assignment_submissions",
            "users",
            ["graded_by"],
            ["id"],
        )


def downgrade() -> None:
    op.drop_constraint("fk_assignment_submissions_graded_by_users", "assignment_submissions", type_="foreignkey")

    op.drop_index(op.f("ix_assignment_submissions_graded_by"), table_name="assignment_submissions")
    op.drop_index(op.f("ix_assignment_submissions_graded_at"), table_name="assignment_submissions")
    op.drop_index(op.f("ix_assignment_submissions_submitted_at"), table_name="assignment_submissions")

    op.drop_column("assignment_submissions", "report_file_size")
    op.drop_column("assignment_submissions", "report_file_path")
    op.drop_column("assignment_submissions", "report_file_name")
    op.drop_column("assignment_submissions", "graded_by")
    op.drop_column("assignment_submissions", "graded_at")
    op.drop_column("assignment_submissions", "submitted_at")
