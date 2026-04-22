import csv
import asyncio
import datetime
import io
import json
import logging
import re
import time
import urllib.parse
from typing import AsyncIterator, List

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user, get_current_user, get_db, get_teacher_user, get_user_by_token
from app.core.config import settings
from app.core.permission import get_allowed_device_ids, require_can_access_device_history
from app.db.models import (
    AIConversation,
    AIConversationMessage,
    Class,
    ClassDeviceBind,
    Device,
    GrowthRecord,
    PlantProfile,
    SensorReading,
    User,
)
from app.db.session import SessionLocal
from app.schemas.telemetry import (
    AIConversationAskRequest,
    AIConversationCreateRequest,
    AIConversationDetailResponse,
    AIConversationMessageResponse,
    AIConversationPinRequest,
    AIConversationRenameRequest,
    AIConversationSummaryResponse,
    AIScienceAskRequest,
    AIScienceAskResponse,
    ControlRequest,
    DeviceCreateRequest,
    DeviceResponse,
    ExportRequest,
    TelemetryData,
    TelemetryResponse,
)
from app.services.ai_science_service import (
    align_citations_with_answer,
    ask_science_assistant,
    generate_conversation_title,
    stream_science_assistant_with_source,
)
from app.services.ai_audit_service import infer_fallback_reason, record_ai_audit
from app.services.telemetry_hub_service import TelemetryHub


router = APIRouter()
telemetry_hub = TelemetryHub()
logger = logging.getLogger(__name__)
DEFAULT_CONVERSATION_TITLE = "新对话"
CAMERA_MAX_FRAME_BYTES = 512 * 1024
CAMERA_FRAME_TTL_SECONDS = 20
CAMERA_STREAM_BOUNDARY = "frame"
CAMERA_STREAM_IDLE_SECONDS = 0.2
camera_frames: dict[int, dict[str, object]] = {}
camera_frames_lock = asyncio.Lock()


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def _resolve_camera_stream_user(db: Session, token: str | None, authorization: str | None) -> User:
    auth_token = token or _extract_bearer_token(authorization)
    user = get_user_by_token(auth_token, db) if auth_token else None
    if not user:
        raise HTTPException(status_code=401, detail="未授权访问摄像头流")
    return user


async def _set_camera_frame(device_id: int, frame_bytes: bytes) -> None:
    async with camera_frames_lock:
        camera_frames[device_id] = {
            "frame_bytes": frame_bytes,
            "updated_at": time.time(),
        }


async def _get_camera_frame(device_id: int) -> tuple[bytes | None, float | None]:
    async with camera_frames_lock:
        payload = camera_frames.get(device_id)
    if not payload:
        return None, None

    frame_bytes = payload.get("frame_bytes")
    updated_at = payload.get("updated_at")

    if not isinstance(frame_bytes, (bytes, bytearray)) or not isinstance(updated_at, (int, float)):
        return None, None

    if (time.time() - float(updated_at)) > CAMERA_FRAME_TTL_SECONDS:
        return None, None

    return bytes(frame_bytes), float(updated_at)


async def _camera_mjpeg_generator(device_id: int) -> AsyncIterator[bytes]:
    last_sent_at = 0.0
    while True:
        frame_bytes, updated_at = await _get_camera_frame(device_id)
        if frame_bytes is None or updated_at is None:
            await asyncio.sleep(CAMERA_STREAM_IDLE_SECONDS)
            continue

        if updated_at <= last_sent_at:
            await asyncio.sleep(CAMERA_STREAM_IDLE_SECONDS)
            continue

        last_sent_at = updated_at
        header = (
            f"--{CAMERA_STREAM_BOUNDARY}\r\n"
            "Content-Type: image/jpeg\r\n"
            f"Content-Length: {len(frame_bytes)}\r\n\r\n"
        ).encode("ascii")
        yield header + frame_bytes + b"\r\n"
        await asyncio.sleep(0.02)


def _build_camera_stream_response(device_id: int) -> StreamingResponse:
    return StreamingResponse(
        _camera_mjpeg_generator(device_id),
        media_type=f"multipart/x-mixed-replace; boundary={CAMERA_STREAM_BOUNDARY}",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _ensure_ai_conversation_schema_ready(db: Session) -> None:
    try:
        bind = db.get_bind()
        inspector = inspect(bind)
        tables = set(inspector.get_table_names())
        required = {"ai_conversations", "ai_conversation_messages"}
        missing = sorted(required - tables)
        if missing:
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI 会话功能尚未初始化，请先执行数据库迁移："
                    "python -m alembic upgrade head"
                ),
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("failed to inspect ai conversation schema: %s", exc)


def _resolve_latest_reading_for_ai(
    db: Session,
    current_user: User,
    request: AIScienceAskRequest | AIConversationAskRequest,
) -> SensorReading | None:
    if request.device_id:
        device = db.query(Device).filter(Device.id == request.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        require_can_access_device_history(db, current_user, request.device_id)
        return (
            db.query(SensorReading)
            .filter(SensorReading.device_id == request.device_id)
            .order_by(desc(SensorReading.timestamp))
            .first()
        )

    if current_user.role == "admin":
        return db.query(SensorReading).order_by(desc(SensorReading.timestamp)).first()

    class_ids: List[int] = []
    if current_user.role == "student" and current_user.class_id:
        class_ids = [current_user.class_id]
    elif current_user.role == "teacher":
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == current_user.id).all()]

    if not class_ids:
        return None

    bind = (
        db.query(ClassDeviceBind)
        .filter(ClassDeviceBind.class_id.in_(class_ids))
        .order_by(desc(ClassDeviceBind.id))
        .first()
    )
    if not bind:
        return None

    return (
        db.query(SensorReading)
        .filter(SensorReading.device_id == bind.device_id)
        .order_by(desc(SensorReading.timestamp))
        .first()
    )


def _normalize_conversation_title(title: str | None) -> str:
    normalized = re.sub(r"\s+", " ", (title or "").strip())
    if not normalized:
        return DEFAULT_CONVERSATION_TITLE
    return normalized[:120]


def _get_conversation_or_404(db: Session, current_user: User, conversation_id: int) -> AIConversation:
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


def _serialize_citations(citations: list[dict[str, str]] | None) -> str | None:
    if not citations:
        return None
    try:
        return json.dumps(citations, ensure_ascii=False)
    except Exception:
        return None


def _parse_citations(citations_json: str | None) -> list[dict[str, str]]:
    if not citations_json:
        return []
    try:
        parsed = json.loads(citations_json)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except Exception:
        return []
    return []


def _message_to_response(message: AIConversationMessage) -> AIConversationMessageResponse:
    return AIConversationMessageResponse(
        id=message.id,
        role=str(message.role),
        content=message.content,
        reasoning=message.reasoning,
        source=message.source,
        model=message.model,
        citations=_parse_citations(message.citations_json),
        web_search_notice=message.web_search_notice,
        status=str(message.status or "done"),
        created_at=message.created_at,
    )


def _load_conversation_history(db: Session, conversation_id: int, max_turns: int = 10) -> list[dict[str, str]]:
    rows = (
        db.query(AIConversationMessage)
        .filter(AIConversationMessage.conversation_id == conversation_id)
        .order_by(desc(AIConversationMessage.created_at), desc(AIConversationMessage.id))
        .limit(max_turns * 2)
        .all()
    )

    history: list[dict[str, str]] = []
    for item in reversed(rows):
        content = (item.content or "").strip()
        if item.role not in {"user", "assistant"}:
            continue
        if item.status != "done" or not content:
            continue
        history.append(
            {
                "role": item.role,
                "content": content[:500],
            }
        )
    return history[-max_turns:]


def _build_conversation_summary(db: Session, conversation: AIConversation) -> AIConversationSummaryResponse:
    message_count = (
        db.query(AIConversationMessage)
        .filter(AIConversationMessage.conversation_id == conversation.id)
        .count()
    )
    latest_message = (
        db.query(AIConversationMessage)
        .filter(AIConversationMessage.conversation_id == conversation.id)
        .order_by(desc(AIConversationMessage.created_at), desc(AIConversationMessage.id))
        .first()
    )
    preview = None
    if latest_message and latest_message.content:
        preview = re.sub(r"\s+", " ", latest_message.content.strip())[:80]

    return AIConversationSummaryResponse(
        id=conversation.id,
        title=conversation.title,
        is_pinned=bool(conversation.is_pinned),
        pinned_at=conversation.pinned_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_at=conversation.last_message_at,
        message_count=message_count,
        preview=preview,
    )


@router.post("/api/telemetry")
async def receive_telemetry(
    data: TelemetryData,
    db: Session = Depends(get_db),
    x_device_token: str = Header(None),
):
    if x_device_token != settings.device_token:
        raise HTTPException(status_code=401, detail="设备认证失败")
    try:
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        new_reading = SensorReading(
            device_id=data.device_id,
            temp=data.temp,
            humidity=data.humidity,
            soil_moisture=data.soil_moisture,
            light=data.light,
        )
        db.add(new_reading)

        device.last_seen = datetime.datetime.utcnow()
        device.status = 1

        db.commit()
        db.refresh(new_reading)

        await telemetry_hub.broadcast(
            data.device_id,
            {
                "type": "telemetry_update",
                "device_id": data.device_id,
                "timestamp": new_reading.timestamp.isoformat() if new_reading.timestamp else None,
                "telemetry": {
                    "temp": float(new_reading.temp) if new_reading.temp is not None else None,
                    "humidity": float(new_reading.humidity) if new_reading.humidity is not None else None,
                    "soil_moisture": float(new_reading.soil_moisture) if new_reading.soil_moisture is not None else None,
                    "light": float(new_reading.light) if new_reading.light is not None else None,
                },
                "actuators": {
                    "pump_state": device.pump_state,
                    "fan_state": device.fan_state,
                    "fan_speed": device.fan_speed if device.fan_speed is not None else 100,
                    "light_state": device.light_state,
                    "light_brightness": device.light_brightness if device.light_brightness is not None else 100,
                },
            },
        )

        return {
            "status": "success",
            "id": new_reading.id,
            "commands": {
                "pump": device.pump_state,
                "fan": device.fan_state,
                "fan_speed": device.fan_speed if device.fan_speed is not None else 100,
                "light": device.light_state,
                "light_brightness": device.light_brightness if device.light_brightness is not None else 100,
            },
        }
    except OperationalError:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="遥测数据处理失败，请检查上报格式")


@router.post("/api/devices/{device_id}/camera")
async def upload_camera_frame(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    x_device_token: str = Header(None),
):
    if x_device_token != settings.device_token:
        raise HTTPException(status_code=401, detail="设备认证失败")

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if content_type and content_type not in {"image/jpeg", "image/jpg", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="仅支持 JPEG 图片上传")

    frame_bytes = await request.body()
    if not frame_bytes:
        raise HTTPException(status_code=400, detail="未接收到图片数据")
    if len(frame_bytes) > CAMERA_MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail=f"图片体积过大，最大支持 {CAMERA_MAX_FRAME_BYTES // 1024}KB")

    await _set_camera_frame(device_id, frame_bytes)

    if not device.has_camera:
        device.has_camera = True
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("failed to persist has_camera for device %s: %s", device_id, exc)

    return {
        "status": "success",
        "device_id": device_id,
        "bytes": len(frame_bytes),
    }


@router.get("/api/devices/{device_id}/camera/stream")
async def stream_camera(
    device_id: int,
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    current_user = _resolve_camera_stream_user(db, token, authorization)

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    if not device.has_camera:
        raise HTTPException(status_code=404, detail="该设备未启用摄像头")

    require_can_access_device_history(db, current_user, device_id)
    return _build_camera_stream_response(device_id)


@router.get("/api/legacy/history/{device_id}", response_model=List[TelemetryResponse])
async def get_history(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    require_can_access_device_history(db, current_user, device_id)

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device_id)
        .order_by(desc(SensorReading.timestamp))
        .limit(20)
        .all()
    )
    return readings


@router.get("/api/devices", response_model=List[DeviceResponse])
async def get_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed_device_ids = get_allowed_device_ids(db, current_user)
    if allowed_device_ids is None:
        return db.query(Device).all()
    if not allowed_device_ids:
        return []
    return db.query(Device).filter(Device.id.in_(allowed_device_ids)).all()


@router.post("/api/devices", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    new_device = Device(
        device_name=device_data.device_name,
        status=device_data.status,
        pump_state=device_data.pump_state,
        fan_state=device_data.fan_state,
        fan_speed=device_data.fan_speed if device_data.fan_speed is not None else 100,
        light_state=device_data.light_state,
        light_brightness=device_data.light_brightness if device_data.light_brightness is not None else 100,
        has_camera=bool(device_data.has_camera),
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@router.post("/api/control/{device_id}")
async def control_device(
    device_id: int,
    data: ControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    if data.pump_state is not None:
        device.pump_state = data.pump_state
    if data.fan_state is not None:
        device.fan_state = data.fan_state
    if data.fan_speed is not None:
        device.fan_speed = data.fan_speed
    if data.light_state is not None:
        device.light_state = data.light_state
    if data.light_brightness is not None:
        device.light_brightness = data.light_brightness

    db.commit()
    db.refresh(device)

    latest = db.query(SensorReading).filter(SensorReading.device_id == device_id).order_by(desc(SensorReading.timestamp)).first()
    await telemetry_hub.broadcast(
        device_id,
        {
            "type": "control_update",
            "device_id": device_id,
            "timestamp": latest.timestamp.isoformat() if latest and latest.timestamp else None,
            "telemetry": {
                "temp": float(latest.temp) if latest and latest.temp is not None else None,
                "humidity": float(latest.humidity) if latest and latest.humidity is not None else None,
                "soil_moisture": float(latest.soil_moisture) if latest and latest.soil_moisture is not None else None,
                "light": float(latest.light) if latest and latest.light is not None else None,
            },
            "actuators": {
                "pump_state": device.pump_state,
                "fan_state": device.fan_state,
                "fan_speed": device.fan_speed if device.fan_speed is not None else 100,
                "light_state": device.light_state,
                "light_brightness": device.light_brightness if device.light_brightness is not None else 100,
            },
        },
    )

    return {"status": "success", "device_id": device_id}


@router.get("/api/ai/conversations", response_model=list[AIConversationSummaryResponse])
async def list_ai_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversations = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(
            desc(AIConversation.is_pinned),
            desc(AIConversation.pinned_at),
            desc(AIConversation.last_message_at),
            desc(AIConversation.updated_at),
            desc(AIConversation.id),
        )
        .all()
    )
    return [_build_conversation_summary(db, item) for item in conversations]


@router.post("/api/ai/conversations", response_model=AIConversationSummaryResponse)
async def create_ai_conversation(
    request: AIConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = AIConversation(
        user_id=current_user.id,
        title=_normalize_conversation_title(request.title),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _build_conversation_summary(db, conversation)


@router.get("/api/ai/conversations/{conversation_id}", response_model=AIConversationDetailResponse)
async def get_ai_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)
    messages = (
        db.query(AIConversationMessage)
        .filter(AIConversationMessage.conversation_id == conversation.id)
        .order_by(AIConversationMessage.created_at, AIConversationMessage.id)
        .all()
    )
    return AIConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        is_pinned=bool(conversation.is_pinned),
        pinned_at=conversation.pinned_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_at=conversation.last_message_at,
        messages=[_message_to_response(item) for item in messages],
    )


@router.patch("/api/ai/conversations/{conversation_id}/title", response_model=AIConversationSummaryResponse)
async def rename_ai_conversation(
    conversation_id: int,
    request: AIConversationRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)
    conversation.title = _normalize_conversation_title(request.title)
    conversation.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    return _build_conversation_summary(db, conversation)


@router.patch("/api/ai/conversations/{conversation_id}/pin", response_model=AIConversationSummaryResponse)
async def pin_ai_conversation(
    conversation_id: int,
    request: AIConversationPinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)

    conversation.is_pinned = bool(request.is_pinned)
    conversation.pinned_at = datetime.datetime.utcnow() if conversation.is_pinned else None
    conversation.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(conversation)
    return _build_conversation_summary(db, conversation)


@router.delete("/api/ai/conversations/{conversation_id}")
async def delete_ai_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)
    db.delete(conversation)
    db.commit()
    return {"status": "success"}


@router.post("/api/ai/conversations/{conversation_id}/science-assistant", response_model=AIScienceAskResponse)
async def ask_ai_science_assistant_in_conversation(
    conversation_id: int,
    request: AIConversationAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    start_ts = time.perf_counter()
    latest = _resolve_latest_reading_for_ai(db, current_user, request)
    conversation_history = _load_conversation_history(db, conversation.id)
    is_first_question = len(conversation_history) == 0
    selected_model = settings.ai_reasoner_model if request.enable_deep_thinking else settings.ai_chat_model

    db.add(
        AIConversationMessage(
            conversation_id=conversation.id,
            role="user",
            content=question,
            status="done",
        )
    )

    try:
        answer, source, response_meta = await ask_science_assistant(
            question,
            latest,
            conversation_history=conversation_history,
            user_role=current_user.role,
            enable_deep_thinking=request.enable_deep_thinking,
            enable_web_search=request.enable_web_search,
        )
    except Exception as exc:
        logger.exception("ask_ai_science_assistant_in_conversation failed: %s", exc)
        raise HTTPException(status_code=503, detail="AI 助手暂时不可用，请稍后重试") from exc

    db.add(
        AIConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            reasoning=None,
            source=source,
            model=str(response_meta.get("model") or selected_model),
            citations_json=_serialize_citations(response_meta.get("citations") or []),
            web_search_notice=response_meta.get("web_search_notice"),
            status="done",
        )
    )

    if is_first_question and conversation.title == DEFAULT_CONVERSATION_TITLE:
        conversation.title = _normalize_conversation_title(await generate_conversation_title(question))

    now = datetime.datetime.utcnow()
    conversation.last_message_at = now
    conversation.updated_at = now
    db.commit()

    latency_ms = int((time.perf_counter() - start_ts) * 1000)
    record_ai_audit(
        operator_id=current_user.id,
        operation_type="ai_science",
        source=source,
        latency_ms=latency_ms,
        prompt_text=question,
        output_text=answer,
        fallback_reason=infer_fallback_reason(source),
        extra={
            "conversation_id": conversation.id,
            "device_id": request.device_id,
            "model": response_meta.get("model"),
            "deep_thinking": bool(response_meta.get("deep_thinking")),
            "web_search_enabled": bool(response_meta.get("web_search_enabled")),
            "web_search_used": bool(response_meta.get("web_search_used")),
            "citations_count": len(response_meta.get("citations") or []),
        },
    )

    return AIScienceAskResponse(
        answer=answer,
        source=source,
        model=str(response_meta.get("model") or selected_model),
        deep_thinking=bool(response_meta.get("deep_thinking")),
        web_search_enabled=bool(response_meta.get("web_search_enabled")),
        web_search_used=bool(response_meta.get("web_search_used")),
        web_search_notice=response_meta.get("web_search_notice"),
        citations=response_meta.get("citations") or [],
    )


@router.post("/api/ai/conversations/{conversation_id}/science-assistant/stream")
async def stream_ai_science_assistant_in_conversation(
    conversation_id: int,
    request: AIConversationAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_ai_conversation_schema_ready(db)
    conversation = _get_conversation_or_404(db, current_user, conversation_id)
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    latest = _resolve_latest_reading_for_ai(db, current_user, request)
    conversation_history = _load_conversation_history(db, conversation.id)
    is_first_question = len(conversation_history) == 0
    selected_model = settings.ai_reasoner_model if request.enable_deep_thinking else settings.ai_chat_model

    db.add(
        AIConversationMessage(
            conversation_id=conversation.id,
            role="user",
            content=question,
            status="done",
        )
    )
    conversation.last_message_at = datetime.datetime.utcnow()
    conversation.updated_at = datetime.datetime.utcnow()
    db.commit()

    async def event_generator():
        start_ts = time.perf_counter()
        source_used = "unknown"
        sent_meta = False
        output_parts: list[str] = []
        reasoning_parts: list[str] = []
        stream_error: str | None = None
        response_meta: dict[str, object] = {
            "model": selected_model,
            "deep_thinking": request.enable_deep_thinking,
            "web_search_enabled": request.enable_web_search,
            "web_search_used": False,
            "web_search_notice": None,
            "citations": [],
        }

        try:
            async for chunk_dict, chunk_source, chunk_meta in stream_science_assistant_with_source(
                question,
                latest,
                conversation_history=conversation_history,
                user_role=current_user.role,
                enable_deep_thinking=request.enable_deep_thinking,
                enable_web_search=request.enable_web_search,
            ):
                source_used = chunk_source
                if chunk_meta:
                    response_meta = chunk_meta
                if not sent_meta:
                    sent_meta = True
                    meta_payload = {"source": source_used, **response_meta}
                    yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

                text_part = chunk_dict.get("text") or ""
                reasoning_part = chunk_dict.get("reasoning") or ""

                if text_part:
                    output_parts.append(text_part)
                if reasoning_part:
                    reasoning_parts.append(reasoning_part)

                payload = {}
                if text_part:
                    payload["text"] = text_part
                if reasoning_part:
                    payload["reasoning"] = reasoning_part

                if payload:
                    yield f"event: token\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            if output_parts:
                source_used = "stream-error"
                stream_error = "stream_failed_partial"
                if not sent_meta:
                    sent_meta = True
                    meta_payload = {"source": source_used, **response_meta}
                    yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"
                yield f"event: error\ndata: {json.dumps({'message': '连接中断，已保留已生成内容'}, ensure_ascii=False)}\n\n"
                yield "event: done\ndata: {}\n\n"
            else:
                logger.exception("stream_ai_science_assistant_in_conversation failed: %s", exc)
                source_used = "stream-error"
                stream_error = "stream_failed_no_output"
                if not sent_meta:
                    sent_meta = True
                    meta_payload = {"source": source_used, **response_meta}
                    yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"
                yield f"event: error\ndata: {json.dumps({'message': 'AI 助手暂时不可用，请稍后重试'}, ensure_ascii=False)}\n\n"
                yield "event: done\ndata: {}\n\n"
        finally:
            final_answer = "".join(output_parts).strip()
            final_reasoning = "".join(reasoning_parts).strip()

            if bool(response_meta.get("web_search_enabled")) and final_answer:
                aligned_answer, aligned_citations, aligned_notice = align_citations_with_answer(
                    final_answer,
                    list(response_meta.get("citations") or []),
                    response_meta.get("web_search_notice"),
                )
                final_answer = aligned_answer
                response_meta["citations"] = aligned_citations
                response_meta["web_search_notice"] = aligned_notice
                response_meta["web_search_used"] = bool(aligned_citations)

            if final_answer:
                db.add(
                    AIConversationMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=final_answer,
                        reasoning=final_reasoning or None,
                        source=source_used,
                        model=str(response_meta.get("model") or selected_model),
                        citations_json=_serialize_citations(response_meta.get("citations") or []),
                        web_search_notice=response_meta.get("web_search_notice"),
                        status="done",
                    )
                )

            if is_first_question and conversation.title == DEFAULT_CONVERSATION_TITLE:
                conversation.title = _normalize_conversation_title(await generate_conversation_title(question))

            now = datetime.datetime.utcnow()
            conversation.last_message_at = now
            conversation.updated_at = now

            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to persist conversation stream result")

            latency_ms = int((time.perf_counter() - start_ts) * 1000)
            record_ai_audit(
                operator_id=current_user.id,
                operation_type="ai_stream",
                source=source_used,
                latency_ms=latency_ms,
                prompt_text=question,
                output_text=final_answer,
                fallback_reason=infer_fallback_reason(source_used),
                extra={
                    "conversation_id": conversation.id,
                    "device_id": request.device_id,
                    "stream": True,
                    "sent_meta": sent_meta,
                    "chunk_count": len(output_parts),
                    "stream_error": stream_error,
                    "model": response_meta.get("model"),
                    "deep_thinking": bool(response_meta.get("deep_thinking")),
                    "web_search_enabled": bool(response_meta.get("web_search_enabled")),
                    "web_search_used": bool(response_meta.get("web_search_used")),
                    "citations_count": len(response_meta.get("citations") or []),
                    "rag_enabled": settings.rag_enabled,
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/ai/science-assistant", response_model=AIScienceAskResponse)
async def ask_ai_science_assistant(
    request: AIScienceAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_ts = time.perf_counter()
    latest = _resolve_latest_reading_for_ai(db, current_user, request)
    conversation_history = [item.model_dump() for item in request.conversation_history] if request.conversation_history else []
    selected_model = settings.ai_reasoner_model if request.enable_deep_thinking else settings.ai_chat_model
    try:
        answer, source, response_meta = await ask_science_assistant(
            request.question,
            latest,
            conversation_history=conversation_history,
            user_role=current_user.role,
            enable_deep_thinking=request.enable_deep_thinking,
            enable_web_search=request.enable_web_search,
        )
    except Exception as exc:
        logger.exception("ask_ai_science_assistant failed: %s", exc)
        raise HTTPException(status_code=503, detail="AI 助手暂时不可用，请稍后重试") from exc

    latency_ms = int((time.perf_counter() - start_ts) * 1000)
    record_ai_audit(
        operator_id=current_user.id,
        operation_type="ai_science",
        source=source,
        latency_ms=latency_ms,
        prompt_text=request.question,
        output_text=answer,
        fallback_reason=infer_fallback_reason(source),
        extra={
            "device_id": request.device_id,
            "model": response_meta.get("model"),
            "deep_thinking": bool(response_meta.get("deep_thinking")),
            "web_search_enabled": bool(response_meta.get("web_search_enabled")),
            "web_search_used": bool(response_meta.get("web_search_used")),
            "citations_count": len(response_meta.get("citations") or []),
        },
    )

    return AIScienceAskResponse(
        answer=answer,
        source=source,
        model=str(response_meta.get("model") or selected_model),
        deep_thinking=bool(response_meta.get("deep_thinking")),
        web_search_enabled=bool(response_meta.get("web_search_enabled")),
        web_search_used=bool(response_meta.get("web_search_used")),
        web_search_notice=response_meta.get("web_search_notice"),
        citations=response_meta.get("citations") or [],
    )


@router.post("/api/ai/science-assistant/stream")
async def stream_ai_science_assistant(
    request: AIScienceAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = _resolve_latest_reading_for_ai(db, current_user, request)
    conversation_history = [item.model_dump() for item in request.conversation_history] if request.conversation_history else []
    selected_model = settings.ai_reasoner_model if request.enable_deep_thinking else settings.ai_chat_model

    async def event_generator():
        start_ts = time.perf_counter()
        source_used = "unknown"
        sent_meta = False
        output_parts: list[str] = []
        stream_error: str | None = None
        response_meta: dict[str, object] = {
            "model": selected_model,
            "deep_thinking": request.enable_deep_thinking,
            "web_search_enabled": request.enable_web_search,
            "web_search_used": False,
            "web_search_notice": None,
            "citations": [],
        }

        try:
            async for chunk_dict, chunk_source, chunk_meta in stream_science_assistant_with_source(
                request.question,
                latest,
                conversation_history=conversation_history,
                user_role=current_user.role,
                enable_deep_thinking=request.enable_deep_thinking,
                enable_web_search=request.enable_web_search,
            ):
                source_used = chunk_source
                if chunk_meta:
                    response_meta = chunk_meta
                if not sent_meta:
                    sent_meta = True
                    meta_payload = {"source": source_used, **response_meta}
                    yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"
                
                text_part = chunk_dict.get("text") or ""
                reasoning_part = chunk_dict.get("reasoning") or ""
                
                output_parts.append(text_part)
                
                payload = {}
                if text_part:
                    payload["text"] = text_part
                if reasoning_part:
                    payload["reasoning"] = reasoning_part
                    
                if payload:
                    yield f"event: token\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            if output_parts:
                source_used = "stream-error"
                stream_error = "stream_failed_partial"
                if not sent_meta:
                    sent_meta = True
                    meta_payload = {"source": source_used, **response_meta}
                    yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"
                yield f"event: error\ndata: {json.dumps({'message': '连接中断，已保留已生成内容'}, ensure_ascii=False)}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            logger.exception("stream_ai_science_assistant failed: %s", exc)
            source_used = "stream-error"
            stream_error = "stream_failed_no_output"
            if not sent_meta:
                sent_meta = True
                meta_payload = {"source": source_used, **response_meta}
                yield f"event: meta\ndata: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"
            yield f"event: error\ndata: {json.dumps({'message': 'AI 助手暂时不可用，请稍后重试'}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        finally:
            final_answer = "".join(output_parts).strip()
            if bool(response_meta.get("web_search_enabled")) and final_answer:
                aligned_answer, aligned_citations, aligned_notice = align_citations_with_answer(
                    final_answer,
                    list(response_meta.get("citations") or []),
                    response_meta.get("web_search_notice"),
                )
                final_answer = aligned_answer
                response_meta["citations"] = aligned_citations
                response_meta["web_search_notice"] = aligned_notice
                response_meta["web_search_used"] = bool(aligned_citations)

            latency_ms = int((time.perf_counter() - start_ts) * 1000)
            record_ai_audit(
                operator_id=current_user.id,
                operation_type="ai_stream",
                source=source_used,
                latency_ms=latency_ms,
                prompt_text=request.question,
                output_text=final_answer,
                fallback_reason=infer_fallback_reason(source_used),
                extra={
                    "device_id": request.device_id,
                    "stream": True,
                    "sent_meta": sent_meta,
                    "chunk_count": len(output_parts),
                    "stream_error": stream_error,
                    "model": response_meta.get("model"),
                    "deep_thinking": bool(response_meta.get("deep_thinking")),
                    "web_search_enabled": bool(response_meta.get("web_search_enabled")),
                    "web_search_used": bool(response_meta.get("web_search_used")),
                    "citations_count": len(response_meta.get("citations") or []),
                    "rag_enabled": settings.rag_enabled,
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ws/telemetry/{device_id}")
async def telemetry_ws(websocket: WebSocket, device_id: int):
    token = websocket.query_params.get("token", "")
    db = SessionLocal()
    try:
        user = get_user_by_token(token, db)
        if not user:
            await websocket.close(code=1008)
            return

        await telemetry_hub.connect(device_id, websocket)

        device = db.query(Device).filter(Device.id == device_id).first()
        latest = db.query(SensorReading).filter(SensorReading.device_id == device_id).order_by(desc(SensorReading.timestamp)).first()
        await websocket.send_json(
            {
                "type": "snapshot",
                "device_id": device_id,
                "telemetry": {
                    "temp": float(latest.temp) if latest and latest.temp is not None else None,
                    "humidity": float(latest.humidity) if latest and latest.humidity is not None else None,
                    "soil_moisture": float(latest.soil_moisture) if latest and latest.soil_moisture is not None else None,
                    "light": float(latest.light) if latest and latest.light is not None else None,
                },
                "actuators": {
                    "pump_state": device.pump_state if device else 0,
                    "fan_state": device.fan_state if device else 0,
                    "fan_speed": (device.fan_speed if device and device.fan_speed is not None else 100),
                    "light_state": device.light_state if device else 0,
                    "light_brightness": (device.light_brightness if device and device.light_brightness is not None else 100),
                },
                "timestamp": latest.timestamp.isoformat() if latest and latest.timestamp else None,
            }
        )

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_hub.disconnect(device_id, websocket)
    finally:
        db.close()


@router.post("/api/telemetry/export")
async def export_telemetry(
    request: ExportRequest,
    export_format: str = "csv",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        device = db.query(Device).filter(Device.id == request.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        if current_user.role == 'student':
            if not current_user.class_id:
                raise HTTPException(status_code=403, detail="尚未分配班级，无权导出数据")
            bind = db.query(ClassDeviceBind).filter(
                ClassDeviceBind.class_id == current_user.class_id,
                ClassDeviceBind.device_id == request.device_id,
            ).first()
            if not bind:
                raise HTTPException(status_code=403, detail="无权导出此设备数据（非本班设备）")

        try:
            start_date = datetime.datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(request.end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")

        now = datetime.datetime.now()
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
        if end_date > now:
            raise HTTPException(status_code=400, detail="结束日期不能是未来时间")
        if (end_date - start_date).days > 31:
            raise HTTPException(status_code=400, detail="日期范围不能超过 31 天")

        end_date_inclusive = end_date + datetime.timedelta(days=1)
        readings_query = (
            db.query(SensorReading)
            .filter(SensorReading.device_id == request.device_id)
            .filter(SensorReading.timestamp >= start_date)
            .filter(SensorReading.timestamp < end_date_inclusive)
            .order_by(SensorReading.timestamp)
        )

        first_reading = readings_query.first()
        if not first_reading:
            raise HTTPException(status_code=404, detail="所选日期范围内没有数据")

        safe_device_name = re.sub(r'[^\w\s-]', '', device.device_name).strip()
        safe_device_name = re.sub(r'\s+', '_', safe_device_name)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        logging.info(f"User {current_user.username} exported {export_format.upper()} data for device {device.id} ({device.device_name})")

        if export_format == "xlsx":
            readings = readings_query.all()
            data = []
            for r in readings:
                data.append(
                    {
                        "时间": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "设备 ID": r.device_id,
                        "设备名称": device.device_name,
                        "温度 (°C)": float(r.temp) if r.temp is not None else "",
                        "湿度 (%)": float(r.humidity) if r.humidity is not None else "",
                        "土壤湿度 (%)": float(r.soil_moisture) if r.soil_moisture is not None else "",
                        "光照强度 (Lx)": float(r.light) if r.light is not None else "",
                    }
                )
            df = pd.DataFrame(data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='SensorData')
            output.seek(0)

            filename = f"sensor_data_{safe_device_name}_{timestamp}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            def iter_csv():
                stream = io.StringIO()
                writer = csv.writer(stream)
                writer.writerow(["时间", "设备 ID", "设备名称", "温度 (°C)", "湿度 (%)", "土壤湿度 (%)", "光照强度 (Lx)"])
                yield "\ufeff" + stream.getvalue()
                stream.seek(0)
                stream.truncate(0)

                for r in readings_query.yield_per(1000):
                    writer.writerow(
                        [
                            r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            r.device_id,
                            device.device_name,
                            float(r.temp) if r.temp is not None else "",
                            float(r.humidity) if r.humidity is not None else "",
                            float(r.soil_moisture) if r.soil_moisture is not None else "",
                            float(r.light) if r.light is not None else "",
                        ]
                    )
                    yield stream.getvalue()
                    stream.seek(0)
                    stream.truncate(0)

            filename = f"sensor_data_{safe_device_name}_{timestamp}.csv"
            media_type = "text/csv"

        encoded_filename = urllib.parse.quote(filename)

        if export_format == "csv":
            return StreamingResponse(
                iter_csv(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
            )

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)}")


@router.get("/api/public/history/{device_id}", response_model=List[TelemetryResponse])
async def get_public_history(device_id: int, limit: int = 20, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    safe_limit = max(1, min(limit, 200))
    readings = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device_id)
        .order_by(desc(SensorReading.timestamp))
        .limit(safe_limit)
        .all()
    )
    return readings


@router.get("/api/public/devices/{device_id}/camera/stream")
async def stream_public_camera(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    if not device.has_camera:
        raise HTTPException(status_code=404, detail="该设备未启用摄像头")
    return _build_camera_stream_response(device_id)


@router.get("/api/public/display")
async def get_display_data(device_id: int = 1, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    latest_reading = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device.id)
        .order_by(desc(SensorReading.timestamp))
        .first()
    )

    plants = db.query(PlantProfile).filter(PlantProfile.status == "growing").limit(4).all()

    recent_records = (
        db.query(GrowthRecord)
        .join(PlantProfile)
        .order_by(desc(GrowthRecord.record_date))
        .limit(5)
        .all()
    )

    records_data = []
    for record in recent_records:
        records_data.append(
            {
                "id": record.id,
                "plant_name": record.plant.plant_name if record.plant else "未知",
                "record_date": record.record_date.isoformat() if record.record_date else None,
                "stage": record.stage,
                "height_cm": float(record.height_cm) if record.height_cm else None,
                "leaf_count": record.leaf_count,
            }
        )

    return {
        "device": {
            "id": device.id,
            "name": device.device_name,
            "status": device.status,
            "pump_state": device.pump_state,
            "fan_state": device.fan_state,
            "light_state": device.light_state,
            "has_camera": bool(device.has_camera),
            "camera_stream_path": (
                f"/api/public/devices/{device.id}/camera/stream" if device.has_camera else None
            ),
        },
        "telemetry": {
            "temp": float(latest_reading.temp) if latest_reading and latest_reading.temp is not None else None,
            "humidity": float(latest_reading.humidity) if latest_reading and latest_reading.humidity is not None else None,
            "soil_moisture": float(latest_reading.soil_moisture) if latest_reading and latest_reading.soil_moisture is not None else None,
            "light": float(latest_reading.light) if latest_reading and latest_reading.light is not None else None,
            "timestamp": latest_reading.timestamp.isoformat() if latest_reading else None,
        },
        "plants": [
            {
                "id": p.id,
                "name": p.plant_name,
                "species": p.species,
                "status": p.status,
            }
            for p in plants
        ],
        "recent_records": records_data,
    }
