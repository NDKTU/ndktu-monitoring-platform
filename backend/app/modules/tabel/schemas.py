from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict

from app.models.tabel_entries.model import TabelCode


class TabelMonthRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    department: str | None = None
    search: str | None = None


class TabelCell(BaseModel):
    day: int
    code: TabelCode | None
    source: Literal["auto", "manual"]


class TabelRow(BaseModel):
    employee_id: int
    full_name: str
    position: str | None
    department: str | None
    cells: list[TabelCell]
    worked_days: int
    work_rate: float


class TabelMonthResponse(BaseModel):
    year: int
    month: int
    days_in_month: int
    working_days: int
    rows: list[TabelRow]


class TabelEntryUpsertRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    employee_id: int
    date: date_type
    code: TabelCode
    comment: str | None = None


class TabelEntryDeleteRequest(BaseModel):
    employee_id: int
    date: date_type


class TabelEntryResult(BaseModel):
    ok: bool
