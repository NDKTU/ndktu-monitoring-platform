from datetime import time

from pydantic import BaseModel, computed_field
from pydantic_settings import SettingsConfigDict


class WorkScheduleCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    start_time: time
    end_time: time
    grace_minutes: int = 0


class WorkScheduleUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    start_time: time
    end_time: time
    grace_minutes: int


class WorkScheduleResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    start_time: time
    end_time: time
    grace_minutes: int
    employee_count: int = 0


class WorkScheduleListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class WorkScheduleListResponse(BaseModel):
    total: int
    page: int
    limit: int
    schedules: list[WorkScheduleResponse]


class WorkScheduleEmployeesRequest(BaseModel):
    employee_ids: list[int]


class WorkScheduleEmployeesResult(BaseModel):
    affected: int


class WorkScheduleEmployeeItem(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    first_name: str
    last_name: str
    third_name: str | None = None

    @computed_field
    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.third_name]
        return " ".join(p for p in parts if p)


class WorkScheduleEmployeesListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class WorkScheduleEmployeesListResponse(BaseModel):
    total: int
    page: int
    limit: int
    employees: list[WorkScheduleEmployeeItem]
