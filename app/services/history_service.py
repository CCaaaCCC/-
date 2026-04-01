from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.permission import require_can_access_device_history
from app.db.models import Device, SensorReading, User


def get_history(db: Session, current_user: User, device_id: int) -> List[Dict[str, Any]]:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        # keep behavior consistent with main.py
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="设备不存在")

    require_can_access_device_history(db, current_user, device_id)

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(20)
        .all()
    )

    result: List[Dict[str, Any]] = []
    for r in readings:
        result.append(
            {
                "id": r.id,
                "device_id": r.device_id,
                "temp": float(r.temp) if r.temp is not None else None,
                "humidity": float(r.humidity) if r.humidity is not None else None,
                "soil_moisture": float(r.soil_moisture) if r.soil_moisture is not None else None,
                "light": float(r.light) if r.light is not None else None,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
        )
    return result

