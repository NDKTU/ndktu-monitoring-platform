from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class UserCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str
    password: str
    is_active: bool | None = True
    role_id: int | None = None


class UserUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    role_id: int | None = None


class RoleSimpleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    username: str
    is_active: bool
    role_id: int | None
    role: RoleSimpleResponse | None = None


class UserListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None
    is_active: bool | None = None
    role_id: int | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    users: list[UserResponse]
