from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(
    tags=["Users"],
    prefix="/users",
)

def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> UserService:
    repository = UserRepository(session)
    return UserService(repository)


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreateRequest,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)


@router.post("/list", response_model=UserListResponse)
async def list_users(
    request: UserListRequest,
    service: UserService = Depends(get_user_service)
):
    return await service.list_users(request)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdateRequest,
    service: UserService = Depends(get_user_service)
):
    updated = await service.update_user(user_id, user)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return deleted
