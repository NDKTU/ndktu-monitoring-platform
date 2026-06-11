from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.core.config import settings
from app.core.db_helper import db_helper
from app.models.users.model import User
from app.modules.auth import utils, schemas

router = APIRouter(tags=["Auth"], prefix="/auth")

@router.post("/login", response_model=schemas.Token)
async def login_access_token(
    session: AsyncSession = Depends(db_helper.session_getter),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> schemas.Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    stmt = select(User).where(User.username == form_data.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not utils.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return schemas.Token(
        access_token=utils.create_access_token(user.id),
        refresh_token=utils.create_refresh_token(user.id),
        token_type="bearer"
    )

@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    data: schemas.RefreshTokenRequest,
    session: AsyncSession = Depends(db_helper.session_getter)
) -> schemas.Token:
    """
    Refresh tokens
    """
    try:
        payload = jwt.decode(
            data.refresh_token, settings.auth.secret_key, algorithms=["HS256"]
        )
        if not payload.get("refresh"):
            raise HTTPException(status_code=403, detail="Invalid refresh token")
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
        
    if not user_id:
        raise HTTPException(status_code=401, detail="Token has no subject")

    stmt = select(User).where(User.id == int(user_id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return schemas.Token(
        access_token=utils.create_access_token(user.id),
        refresh_token=utils.create_refresh_token(user.id),
        token_type="bearer"
    )
