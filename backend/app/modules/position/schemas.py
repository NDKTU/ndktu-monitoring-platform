from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class PositionCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    name: str


class PositionUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    name: str


class PositionResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    name: str


class PositionListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PositionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    positions: list[PositionResponse]
