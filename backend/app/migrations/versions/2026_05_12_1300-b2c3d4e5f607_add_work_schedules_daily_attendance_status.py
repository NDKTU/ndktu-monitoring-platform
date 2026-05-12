"""Add work_schedules and daily_attendance tables, and attendance status fields

Revision ID: b2c3d4e5f607
Revises: a1b2c3d4e5f6
Create Date: 2026-05-12 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f607"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "work_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("grace_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id"),
    )

    status_enum = sa.Enum(
        "ON_TIME",
        "LATE_ARRIVAL",
        "EARLY_LEAVE",
        "LATE_AND_EARLY",
        "NO_ENTER",
        "NO_EXIT",
        name="attendance_status",
    )

    op.create_table(
        "daily_attendance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", status_enum, nullable=True),
        sa.Column("total_working_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("first_enter_time", sa.DateTime(), nullable=True),
        sa.Column("last_exit_time", sa.DateTime(), nullable=True),
        sa.Column("has_no_enter", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_no_exit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "date", name="uq_daily_attendance_employee_date"),
    )

    op.alter_column("attendance", "enter_time", existing_type=sa.DateTime(), nullable=True)
    op.add_column("attendance", sa.Column("working_hours", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("attendance", "working_hours")
    op.alter_column("attendance", "enter_time", existing_type=sa.DateTime(), nullable=False)
    op.drop_table("daily_attendance")
    op.drop_table("work_schedules")
    sa.Enum(name="attendance_status").drop(op.get_bind(), checkfirst=True)
