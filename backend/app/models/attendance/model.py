from app.models.base import Base
from app.models.mixins import IdIntPk

from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employees.model import Employee
    from app.models.cameras.model import Cameras


class Attendance(Base, IdIntPk):

    __tablename__ = "attendance"

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    enter_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enter_image_path: Mapped[str | None] = mapped_column(nullable=True)
    exit_image_path: Mapped[str | None] = mapped_column(nullable=True)
    working_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendances")
    camera: Mapped["Cameras"] = relationship("Cameras", back_populates="attendances")
