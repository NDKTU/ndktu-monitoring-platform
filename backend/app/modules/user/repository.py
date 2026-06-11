from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.utils import get_password_hash

from app.models.users.model import User
from app.modules.user.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserListRequest,
    UserListResponse,
    UserResponse,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(self, user: UserCreateRequest) -> User:
        user_data = user.model_dump()
        user_data["password"] = get_password_hash(user_data["password"])
        db_user = User(**user_data)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def list_users(self, request: UserListRequest) -> UserListResponse:
        from app.core.config import settings
        from sqlalchemy.orm import selectinload

        query = select(User).options(selectinload(User.role)).where(User.username != settings.admin.login)

        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(User.username.ilike(search_term))

        if request.is_active is not None:
            query = query.where(User.is_active == request.is_active)
        if request.role_id is not None:
            query = query.where(User.role_id == request.role_id)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(request.offset).limit(request.limit)
        users_result = await self.session.execute(query)
        user_list = users_result.scalars().all()

        return UserListResponse(
            users=[UserResponse.model_validate(u) for u in user_list],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar()

    async def update_user(self, user_id: int, user: UserUpdateRequest) -> User | None:
        db_user = await self.get_user(user_id)
        if not db_user:
            return None

        update_data = user.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])
        for key, value in update_data.items():
            setattr(db_user, key, value)

        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: int) -> User | None:
        db_user = await self.get_user(user_id)
        if not db_user:
            return None
        await self.session.delete(db_user)
        await self.session.commit()
        return db_user
