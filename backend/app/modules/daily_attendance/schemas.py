from datetime import date as date_type, datetime

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from app.models.daily_attendance.model import AttendanceStatus


class EmployeeShortResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    first_name: str
    last_name: str
    third_name: str | None
    jshir: str
    full_name: str


class DailyAttendanceResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    employee_id: int
    date: date_type
    status: AttendanceStatus | None
    total_working_hours: float
    first_enter_time: datetime | None
    last_exit_time: datetime | None
    has_no_enter: bool
    has_no_exit: bool
    employee: EmployeeShortResponse | None = None


class DailyAttendanceListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    employee_id: int | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    status: AttendanceStatus | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class DailyAttendanceListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[DailyAttendanceResponse]
