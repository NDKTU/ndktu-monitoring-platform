from pydantic import BaseModel, computed_field
from pydantic_settings import SettingsConfigDict


class EmployeeCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    first_name: str
    last_name: str
    third_name: str | None = None
    passport_series: str | None = None
    jshir: str
    in_work: bool | None = False
    image_path: str | None = None
    position: str | None = None
    department: str | None = None


class EmployeeUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    first_name: str | None = None
    last_name: str | None = None
    third_name: str | None = None
    passport_series: str | None = None
    jshir: str | None = None
    in_work: bool | None = None
    image_path: str | None = None
    position: str | None = None
    department: str | None = None


class EmployeeResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    first_name: str
    last_name: str
    third_name: str | None
    passport_series: str | None
    jshir: str
    in_work: bool
    image_path: str | None
    work_schedule_id: int | None = None
    position: str | None = None
    department: str | None = None

    @computed_field
    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.third_name]
        return " ".join(p for p in parts if p)


class EmployeeListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None
    in_work: bool | None = None
    jshir: str | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class EmployeeListResponse(BaseModel):
    total: int
    page: int
    limit: int
    employees: list[EmployeeResponse]
