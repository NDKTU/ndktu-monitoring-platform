"""Add employee position/department and tabel_entries table.

Revision ID: d4e5f6072139
Revises: c3d4e5f60821
Create Date: 2026-05-14 10:00:00.000000

Adds the monthly timesheet ("Tabel") feature:
- employees.position / employees.department — free-text fields shown in the
  timesheet grid and filters.
- tabel_entries — manual per-(employee, date) code overrides. The grid
  auto-derives B (worked) / A (weekend); any other code is a manual override
  stored here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6072139"
down_revision: Union[str, None] = "c3d4e5f60821"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees", sa.Column("position", sa.String(length=120), nullable=True)
    )
    op.add_column(
        "employees", sa.Column("department", sa.String(length=120), nullable=True)
    )

    tabel_code = sa.Enum(
        "B", "A", "V", "VU", "N", "G", "O", "OU", "R", "RP", "S", "P", "F",
        name="tabel_code",
    )

    op.create_table(
        "tabel_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("code", tabel_code, nullable=False),
        sa.Column("comment", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "date", name="uq_tabel_entry_employee_date"),
    )


def downgrade() -> None:
    op.drop_table("tabel_entries")
    sa.Enum(name="tabel_code").drop(op.get_bind(), checkfirst=True)
    op.drop_column("employees", "department")
    op.drop_column("employees", "position")
