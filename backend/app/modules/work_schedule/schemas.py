from datetime import time

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class WorkScheduleCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    employee_id: int
    start_time: time
    end_time: time
    grace_minutes: int = 0


class WorkScheduleUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    start_time: time | None = None
    end_time: time | None = None
    grace_minutes: int | None = None


class WorkScheduleResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    employee_id: int
    start_time: time
    end_time: time
    grace_minutes: int


class WorkScheduleListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    employee_id: int | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class WorkScheduleListResponse(BaseModel):
    total: int
    page: int
    limit: int
    schedules: list[WorkScheduleResponse]
