from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

if TYPE_CHECKING:
    from app.models.employees.model import Employee


class WorkSchedule(Base, IdIntPk, TimestampMixin):

    __tablename__ = "work_schedules"
    __table_args__ = (
        UniqueConstraint(
            "start_time", "end_time", "grace_minutes", name="uq_work_schedule_times"
        ),
    )

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="work_schedule"
    )
