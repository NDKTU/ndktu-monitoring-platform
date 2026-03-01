from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from enum import Enum


class DirectionType(str, Enum):
    EXIT = "exit"
    ENTER = "enter"


class CameraCreateRequest(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
    )
    device_ip: str
    username: str
    password: str
    direction: DirectionType
    is_active: bool | None = False


class CameraUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
    )
    device_ip: str | None = None
    username: str | None = None
    password: str | None = None
    direction: DirectionType | None = None
    is_active: bool | None = None

class CameraResponse(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )
    id: int
    device_ip: str
    username: str
    password: str
    direction: DirectionType
    is_active: bool

class CameraListRequest(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
    )
    page: int = 1
    limit: int = 10
    search: str | None = None
    device_ip: str | None = None
    username: str | None = None
    direction: DirectionType | None = None
    is_active: bool | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class CameraListResponse(BaseModel):
    total: int
    page: int
    limit: int
    cameras: list[CameraResponse]
