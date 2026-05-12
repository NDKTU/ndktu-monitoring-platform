from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class UserCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str
    password: str
    is_active: bool | None = True
    is_superuser: bool | None = False


class UserUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    username: str
    is_active: bool
    is_superuser: bool


class UserListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    users: list[UserResponse]
