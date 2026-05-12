"""Split users into users+employees, rename user_events to attendance,
rename cameras.username to cameras.login

Revision ID: a1b2c3d4e5f6
Revises: 2bc797c12eec
Create Date: 2026-05-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2bc797c12eec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("third_name", sa.String(length=50), nullable=True),
        sa.Column("passport_series", sa.String(length=20), nullable=True),
        sa.Column("jshir", sa.String(length=14), nullable=False),
        sa.Column("in_work", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("image_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jshir"),
        sa.UniqueConstraint("passport_series"),
    )

    # 2. Rename user_events table -> attendance
    op.rename_table("user_events", "attendance")

    # 3. Drop existing rows: old user_id values point to users.id but the new
    # FK targets employees.id. Operators must re-import attendance after
    # populating employees.
    op.execute("DELETE FROM attendance")

    # 4. Drop old FK from attendance.user_id -> users.id, rename column,
    # then add new FK to employees.id
    with op.batch_alter_table("attendance") as batch_op:
        batch_op.drop_constraint("user_events_user_id_fkey", type_="foreignkey")
        batch_op.alter_column("user_id", new_column_name="employee_id")
        batch_op.create_foreign_key(
            "attendance_employee_id_fkey",
            "employees",
            ["employee_id"],
            ["id"],
        )

    # 5. cameras.username -> cameras.login
    op.alter_column("cameras", "username", new_column_name="login")

    # 6. users: drop image and in_work, add is_superuser, tighten password,
    # add unique constraint on username
    op.execute("UPDATE users SET password = '' WHERE password IS NULL")
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.add_column(
        "users",
        sa.Column(
            "is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.drop_column("users", "image")
    op.drop_column("users", "in_work")


def downgrade() -> None:
    # 6. users: restore image, in_work; drop is_superuser; relax password
    op.add_column("users", sa.Column("in_work", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("image", sa.String(), nullable=True))
    op.drop_column("users", "is_superuser")
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        nullable=True,
    )

    # 5. cameras.login -> cameras.username
    op.alter_column("cameras", "login", new_column_name="username")

    # 4. attendance.employee_id -> user_id with FK back to users
    op.execute("DELETE FROM attendance")
    with op.batch_alter_table("attendance") as batch_op:
        batch_op.drop_constraint("attendance_employee_id_fkey", type_="foreignkey")
        batch_op.alter_column("employee_id", new_column_name="user_id")
        batch_op.create_foreign_key(
            "user_events_user_id_fkey",
            "users",
            ["user_id"],
            ["id"],
        )

    # 2. attendance -> user_events
    op.rename_table("attendance", "user_events")

    # 1. Drop employees
    op.drop_table("employees")
