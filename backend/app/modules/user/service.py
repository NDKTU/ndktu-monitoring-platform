from app.modules.user.repository import UserRepository
from app.modules.user.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserListRequest,
    UserListResponse,
    UserResponse
)
from app.models.users.model import User

class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, user: UserCreateRequest) -> User:
        return await self.repository.create_user(user)

    async def list_users(self, request: UserListRequest) -> UserListResponse:
        return await self.repository.list_users(request)

    async def get_user(self, user_id: int) -> User | None:
        return await self.repository.get_user(user_id)

    async def update_user(self, user_id: int, user: UserUpdateRequest) -> User | None:
        return await self.repository.update_user(user_id, user)

    async def delete_user(self, user_id: int) -> User | None:
        return await self.repository.delete_user(user_id)
