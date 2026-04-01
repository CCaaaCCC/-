from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import oauth2_scheme
from app.db.models import User
from app.db.session import SessionLocal


token_blacklist: set[str] = set()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录凭证无效或已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


async def get_teacher_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="权限不足：仅教师或管理员可执行此操作")
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足：仅管理员可执行此操作")
    return current_user


async def get_content_editor(current_user: User = Depends(get_current_user)):
    if current_user.role not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="需要教师或管理员权限")
    return current_user


def get_user_by_token(token: str, db: Session) -> Optional[User]:
    if not token or token in token_blacklist:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.username == username).first()
