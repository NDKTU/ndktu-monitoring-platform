from datetime import date as date_type, datetime
from enum import Enum

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from app.models.daily_attendance.model import AttendanceStatus
from app.models.tabel_entries.model import TabelCode


class SyntheticDayStatus(str, Enum):
    """Statuses for days that have no daily_attendance row at all.

    A row is only written when a terminal reports an event, so a day the person
    never showed up leaves no trace and used to fall out of the list entirely.
    These two are computed while reading and never stored, which is why they stay
    out of AttendanceStatus (a Postgres enum) and out of the status filter.
    """

    ABSENT = "ABSENT"
    DAY_OFF = "DAY_OFF"


DayStatus = AttendanceStatus | SyntheticDayStatus


class EmployeeShortResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    first_name: str | None
    last_name: str | None
    third_name: str | None
    jshir: str
    full_name: str


class DailyAttendanceResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    # None for a synthesised absent/day-off day: it has no row of its own.
    id: int | None = None
    employee_id: int
    date: date_type
    status: DayStatus | None
    total_working_hours: float = 0.0
    first_enter_time: datetime | None = None
    last_exit_time: datetime | None = None
    has_no_enter: bool = False
    has_no_exit: bool = False
    # The tabel mark an administrator set by hand for this day, if any. A day the
    # terminals never saw is not necessarily a truancy — it may be signed off as
    # leave or sick days, and calling that "absent" is a visible falsehood.
    tabel_code: TabelCode | None = None
    tabel_comment: str | None = None
    employee: EmployeeShortResponse | None = None


class DailyAttendanceListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    employee_id: int | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    status: AttendanceStatus | None = None
    # Walk the calendar instead of the stored rows, filling the gaps with
    # ABSENT/DAY_OFF. Needs a single employee to have a calendar to walk.
    fill_absent: bool = False

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class DailyAttendanceListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[DailyAttendanceResponse]
