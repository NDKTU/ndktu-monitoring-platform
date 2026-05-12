from datetime import date as date_type, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

if TYPE_CHECKING:
    from app.models.employees.model import Employee


class AttendanceStatus(str, Enum):
    ON_TIME = "ON_TIME"
    LATE_ARRIVAL = "LATE_ARRIVAL"
    EARLY_LEAVE = "EARLY_LEAVE"
    LATE_AND_EARLY = "LATE_AND_EARLY"
    NO_ENTER = "NO_ENTER"
    NO_EXIT = "NO_EXIT"


class DailyAttendance(Base, IdIntPk, TimestampMixin):

    __tablename__ = "daily_attendance"
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_daily_attendance_employee_date"),)

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus | None] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status"), nullable=True
    )
    total_working_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    first_enter_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_exit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    has_no_enter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_no_exit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="daily_attendances")
