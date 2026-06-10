from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from app.modules.work_schedule.schemas import WorkScheduleResponse


class DepartmentCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    name: str
    work_schedule_id: int | None = None


class DepartmentUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    name: str | None = None
    work_schedule_id: int | None = None


class DepartmentResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    name: str
    work_schedule_id: int | None = None
    work_schedule: WorkScheduleResponse | None = None


class DepartmentListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class DepartmentListResponse(BaseModel):
    total: int
    page: int
    limit: int
    departments: list[DepartmentResponse]
