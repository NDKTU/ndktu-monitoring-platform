from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, Integer, Float
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.attendance.model import Attendance
    from app.models.daily_attendance.model import DailyAttendance
    from app.models.positions.model import Position
    from app.models.departments.model import Department


class Employee(Base, IdIntPk, TimestampMixin):

    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    third_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passport_series: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    jshir: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    in_work: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    work_rate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    
    position_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("positions.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance", back_populates="employee"
    )
    position: Mapped["Position | None"] = relationship(
        "Position", back_populates="employees"
    )
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="employees"
    )
    daily_attendances: Mapped[list["DailyAttendance"]] = relationship(
        "DailyAttendance", back_populates="employee"
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.third_name]
        return " ".join(p for p in parts if p)
