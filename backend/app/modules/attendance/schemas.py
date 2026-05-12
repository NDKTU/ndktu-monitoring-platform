from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from datetime import datetime


class EmployeeShortResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    first_name: str
    last_name: str
    third_name: str | None
    jshir: str
    full_name: str


class AttendanceResponse(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )
    id: int
    employee_id: int
    camera_id: int
    enter_time: datetime | None
    exit_time: datetime | None
    enter_image_path: str | None
    exit_image_path: str | None
    working_hours: float | None
    employee: EmployeeShortResponse | None = None


class AttendanceListRequest(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
    )
    page: int = 1
    limit: int = 10
    employee_id: int | None = None
    camera_id: int | None = None
    enter_time: datetime | None = None
    exit_time: datetime | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class AttendanceListResponse(BaseModel):
    total: int
    page: int
    limit: int
    events: list[AttendanceResponse]
