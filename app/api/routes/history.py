from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.services.history_service import get_history

router = APIRouter()


@router.get("/api/history/{device_id}")
async def get_history_endpoint(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_history(db, current_user, device_id)

