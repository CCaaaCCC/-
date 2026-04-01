import datetime
import io

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_admin_user, get_db
from app.db.models import User, UserOperationLog


router = APIRouter(tags=["logs"])


@router.get("/api/logs/operations")
async def get_operation_logs(
    operation_type: str | None = None,
    operator_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = db.query(UserOperationLog).options(
        selectinload(UserOperationLog.operator),
        selectinload(UserOperationLog.target_user),
    )

    if operation_type:
        query = query.filter(UserOperationLog.operation_type == operation_type)
    if operator_id:
        query = query.filter(UserOperationLog.operator_id == operator_id)
    if start_date:
        query = query.filter(func.date(UserOperationLog.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(UserOperationLog.created_at) <= end_date)

    total = query.count()
    logs = query.order_by(desc(UserOperationLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for log in logs:
        items.append(
            {
                "id": log.id,
                "operator_id": log.operator_id,
                "operator_name": getattr(log.operator, "username", None),
                "operation_type": log.operation_type,
                "target_user_id": log.target_user_id,
                "target_user_name": getattr(log.target_user, "username", None) if log.target_user_id else None,
                "details": log.details,
                "created_at": log.created_at,
            }
        )

    return {"items": items, "total": total}


@router.post("/api/logs/operations/export")
async def export_operation_logs(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = db.query(UserOperationLog).options(
        selectinload(UserOperationLog.operator),
        selectinload(UserOperationLog.target_user),
    )

    if start_date:
        query = query.filter(func.date(UserOperationLog.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(UserOperationLog.created_at) <= end_date)

    logs = query.order_by(desc(UserOperationLog.created_at)).all()

    data = []
    for log in logs:
        data.append(
            {
                "ID": log.id,
                "操作类型": log.operation_type,
                "操作员 ID": log.operator_id,
                "操作员": getattr(log.operator, "username", None),
                "目标用户 ID": log.target_user_id,
                "目标用户": getattr(log.target_user, "username", None) if log.target_user_id else None,
                "详情": log.details,
                "时间": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
            }
        )

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="操作日志")
    output.seek(0)

    filename = f"操作日志_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"
        },
    )
