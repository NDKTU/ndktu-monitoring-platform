from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService
from app.modules.user.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserListRequest,
    UserListResponse,
    UserResponse
)
from app.modules.auth.dependencies import PermissionChecker

router = APIRouter(
    tags=["Users"],
    prefix="/users",
)

def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> UserService:
    repository = UserRepository(session)
    return UserService(repository)


@router.post("/", response_model=UserResponse, dependencies=[Depends(PermissionChecker("users:create_user"))])
async def create_user(
    user: UserCreateRequest,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)


@router.get("/list", response_model=UserListResponse, dependencies=[Depends(PermissionChecker("users:list_users"))])
async def list_users(
    request: UserListRequest = Depends(),
    service: UserService = Depends(get_user_service)
):
    return await service.list_users(request)


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(PermissionChecker("users:get_user"))])
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(PermissionChecker("users:update_user"))])
async def update_user(
    user_id: int,
    user: UserUpdateRequest,
    service: UserService = Depends(get_user_service)
):
    return await service.update_user(user_id, user)


@router.delete("/{user_id}", response_model=UserResponse, dependencies=[Depends(PermissionChecker("users:delete_user"))])
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return await service.delete_user(user_id)
