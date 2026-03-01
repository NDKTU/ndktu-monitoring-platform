from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

class UserCreateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str
    password: str | None = None
    image: str | None = None
    is_active: bool | None = True

class UserUpdateRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    username: str | None = None
    password: str | None = None
    image: str | None = None
    is_active: bool | None = None
    in_work: bool | None = None

class UserResponse(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True, from_attributes=True)
    id: int
    username: str
    password: str | None
    image: str | None
    is_active: bool
    in_work: bool

class UserListRequest(BaseModel):
    model_config = SettingsConfigDict(str_strip_whitespace=True)
    page: int = 1
    limit: int = 10
    search: str | None = None
    is_active: bool | None = None
    in_work: bool | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

class UserListResponse(BaseModel):
    total: int
    page: int
    limit: int
    users: list[UserResponse]
