"""Refactor work_schedules into shared templates linked to employees via FK.

Revision ID: c3d4e5f60821
Revises: b2c3d4e5f607
Create Date: 2026-05-13 10:00:00.000000

Old shape: each work_schedules row had a UNIQUE employee_id, so 70 employees on the
same 09:00-18:00 schedule meant 70 duplicate rows.

New shape: work_schedules holds the unique (start_time, end_time, grace_minutes)
templates. employees.work_schedule_id is a nullable FK pointing to the template.

Data migration is done in-place: copy the DISTINCT triples into a temp table,
populate employees.work_schedule_id by matching on the old triples, drop the
old table and rename the temp table to work_schedules.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f60821"
down_revision: Union[str, None] = "b2c3d4e5f607"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the new templates table under a temporary name.
    op.create_table(
        "work_schedules_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("grace_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "start_time", "end_time", "grace_minutes", name="uq_work_schedule_times"
        ),
    )

    # 2. Seed it with the distinct triples from the existing table.
    op.execute(
        """
        INSERT INTO work_schedules_new (start_time, end_time, grace_minutes)
        SELECT DISTINCT start_time, end_time, grace_minutes FROM work_schedules
        """
    )

    # 3. Add the FK column on employees. Keep it nullable so employees without a
    #    schedule are valid.
    op.add_column(
        "employees",
        sa.Column("work_schedule_id", sa.Integer(), nullable=True),
    )

    # 4. Backfill employees.work_schedule_id by matching the old row's triple.
    op.execute(
        """
        UPDATE employees AS e
        SET work_schedule_id = wsn.id
        FROM work_schedules AS ws
        JOIN work_schedules_new AS wsn
            ON wsn.start_time = ws.start_time
           AND wsn.end_time = ws.end_time
           AND wsn.grace_minutes = ws.grace_minutes
        WHERE ws.employee_id = e.id
        """
    )

    # 5. Drop the old table now that the data has migrated.
    op.drop_table("work_schedules")

    # 6. Rename the new table to take the real name and rename its constraints.
    op.rename_table("work_schedules_new", "work_schedules")
    op.execute("ALTER INDEX work_schedules_new_pkey RENAME TO work_schedules_pkey")
    # The unique constraint already uses its final name (uq_work_schedule_times).

    # 7. Add the FK constraint on employees.work_schedule_id.
    op.create_foreign_key(
        "fk_employees_work_schedule_id",
        "employees",
        "work_schedules",
        ["work_schedule_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 1. Recreate the legacy per-employee table structure.
    op.create_table(
        "work_schedules_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("grace_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.UniqueConstraint("employee_id"),
    )

    # 2. Materialise one row per employee from the template + FK.
    op.execute(
        """
        INSERT INTO work_schedules_old (employee_id, start_time, end_time, grace_minutes)
        SELECT e.id, ws.start_time, ws.end_time, ws.grace_minutes
        FROM employees AS e
        JOIN work_schedules AS ws ON ws.id = e.work_schedule_id
        """
    )

    # 3. Drop the FK column and the template table.
    op.drop_constraint("fk_employees_work_schedule_id", "employees", type_="foreignkey")
    op.drop_column("employees", "work_schedule_id")
    op.drop_table("work_schedules")

    # 4. Rename the legacy table back to work_schedules.
    op.rename_table("work_schedules_old", "work_schedules")
    op.execute("ALTER INDEX work_schedules_old_pkey RENAME TO work_schedules_pkey")
