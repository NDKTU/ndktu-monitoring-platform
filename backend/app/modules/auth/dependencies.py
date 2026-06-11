from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db_helper import db_helper
from app.models.users.model import User
from app.models.rbac.model import Role, Permission
from app.modules.auth.schemas import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    session: AsyncSession = Depends(db_helper.session_getter),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.auth.secret_key, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not token_data.sub:
        raise HTTPException(status_code=401, detail="Token has no subject")

    stmt = select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.id == int(token_data.sub))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, user: User = Depends(get_current_user)):
        if not user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
        user_permissions = [p.name for p in user.role.permissions]
        if self.required_permission not in user_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return True
