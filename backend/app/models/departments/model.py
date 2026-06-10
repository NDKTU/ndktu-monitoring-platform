from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employees.model import Employee
    from app.models.work_schedules.model import WorkSchedule


class Department(Base, IdIntPk, TimestampMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    work_schedule_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("work_schedules.id", ondelete="SET NULL"), nullable=True
    )

    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="department"
    )

    work_schedule: Mapped["WorkSchedule | None"] = relationship(
        "WorkSchedule", back_populates="departments"
    )
