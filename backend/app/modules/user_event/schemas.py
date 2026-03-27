from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict
from datetime import datetime


class UserEventResponse(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )
    id: int
    user_id: int
    camera_id: int
    enter_time: datetime
    exit_time: datetime | None
    enter_image_path: str | None
    exit_image_path: str | None


class UserEventListRequest(BaseModel):
    model_config = SettingsConfigDict(
        str_strip_whitespace=True,
    )
    page: int = 1
    limit: int = 10
    user_id: int | None = None
    camera_id: int | None = None
    enter_time: datetime | None = None
    exit_time: datetime | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class UserEventListResponse(BaseModel):
    total: int
    page: int
    limit: int
    events: list[UserEventResponse]
