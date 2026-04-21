import datetime
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, token_blacklist
from app.core.config import settings
from app.core.security import create_access_token, hash_password, oauth2_scheme, verify_password
from app.core.validators import (
    get_password_rule_text,
    is_strict_password_role,
    validate_email,
    validate_password,
    validate_username,
)
from app.db.models import Class, User
from app.schemas.auth import RegisterRequest, RegisterResponse, Token


router = APIRouter()

LOGIN_ATTEMPT_WINDOW_SECONDS = 5 * 60
LOGIN_MAX_FAILED_ATTEMPTS = 8
_login_failures: dict[str, list[float]] = {}
_login_failures_lock = threading.Lock()


def _prune_failures(timestamps: list[float], now_ts: float) -> list[float]:
    threshold = now_ts - LOGIN_ATTEMPT_WINDOW_SECONDS
    return [ts for ts in timestamps if ts >= threshold]


def _get_login_key(request: Request, username: str) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}:{username.strip().lower()}"


def _enforce_login_rate_limit(key: str) -> None:
    now_ts = time.time()
    with _login_failures_lock:
        recent = _prune_failures(_login_failures.get(key, []), now_ts)
        _login_failures[key] = recent
        if len(recent) < LOGIN_MAX_FAILED_ATTEMPTS:
            return
        retry_after = max(1, int(LOGIN_ATTEMPT_WINDOW_SECONDS - (now_ts - recent[0])))
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="登录失败次数过多，请稍后再试",
        headers={"Retry-After": str(retry_after)},
    )


def _record_login_failure(key: str) -> None:
    now_ts = time.time()
    with _login_failures_lock:
        recent = _prune_failures(_login_failures.get(key, []), now_ts)
        recent.append(now_ts)
        _login_failures[key] = recent


def _clear_login_failures(key: str) -> None:
    with _login_failures_lock:
        _login_failures.pop(key, None)


@router.post("/api/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    token_blacklist.add(token)
    return {"message": "Successfully logged out"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    login_key = _get_login_key(request, form_data.username)
    _enforce_login_rate_limit(login_key)

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        _record_login_failure(login_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_login_failures(login_key)
    access_token_expires = datetime.timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@router.post("/api/auth/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    invite_code = payload.invite_code.strip().upper()

    if not validate_username(username):
        raise HTTPException(
            status_code=400,
            detail="用户名格式无效：只能包含字母、数字、下划线，长度 3-20 位",
        )

    strict_mode = is_strict_password_role(payload.role)
    if not validate_password(payload.password, strict=strict_mode):
        raise HTTPException(status_code=400, detail=f"密码强度不足：{get_password_rule_text(strict_mode)}")

    if payload.email and not validate_email(payload.email):
        raise HTTPException(status_code=400, detail="邮箱格式无效")

    if payload.role == "student" and not (payload.student_id and payload.student_id.strip()):
        raise HTTPException(status_code=400, detail="学生注册需要填写学号")
    if payload.role == "teacher" and not (payload.teacher_id and payload.teacher_id.strip()):
        raise HTTPException(status_code=400, detail="教师注册需要填写工号")

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if payload.student_id and db.query(User).filter(User.student_id == payload.student_id.strip()).first():
        raise HTTPException(status_code=400, detail="学号已存在")
    if payload.teacher_id and db.query(User).filter(User.teacher_id == payload.teacher_id.strip()).first():
        raise HTTPException(status_code=400, detail="工号已存在")

    target_class = (
        db.query(Class)
        .filter(Class.invite_code == invite_code, Class.is_active == True)
        .first()
    )
    if not target_class:
        raise HTTPException(status_code=400, detail="邀请码无效或已失效")

    db_user = User(
        username=username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        real_name=(payload.real_name or "").strip() or None,
        email=(payload.email or "").strip() or None,
        student_id=(payload.student_id or "").strip() or None,
        teacher_id=(payload.teacher_id or "").strip() or None,
        class_id=target_class.id if payload.role == "student" else None,
        is_active=True,
        created_by=target_class.teacher_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return RegisterResponse(
        id=db_user.id,
        username=db_user.username,
        role=db_user.role,
        class_id=db_user.class_id,
        created_by=db_user.created_by,
        message="注册成功，账号已完成绑定",
    )
