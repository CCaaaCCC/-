import datetime
from typing import Optional

import bcrypt
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    """Hash password with passlib, fallback to raw bcrypt for backend-compat issues."""
    try:
        return pwd_context.hash(password)
    except Exception:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("password cannot be longer than 72 bytes")
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with passlib, fallback to raw bcrypt for backend-compat issues."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        if not hashed_password or not hashed_password.startswith("$2"):
            return False
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
        except Exception:
            return False


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
