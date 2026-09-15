"""give an employee a work schedule of their own

Revision ID: a7c3e1d94f20
Revises: 4b67d38f25db
Create Date: 2026-09-15 09:00:00.000000

A schedule could only be reached through a department. An employee with no
department therefore had no schedule, and every one of their days came out with
no status at all — blank in the card, blank in the reports.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3e1d94f20'
down_revision: Union[str, Sequence[str], None] = '4b67d38f25db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'employees', sa.Column('work_schedule_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_employees_work_schedule_id',
        'employees',
        'work_schedules',
        ['work_schedule_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_employees_work_schedule_id', 'employees', type_='foreignkey')
    op.drop_column('employees', 'work_schedule_id')
