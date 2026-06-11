from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import bcrypt

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth.access_token_expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.auth.secret_key, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth.refresh_token_expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject), "refresh": True}
    encoded_jwt = jwt.encode(to_encode, settings.auth.secret_key, algorithm="HS256")
    return encoded_jwt
