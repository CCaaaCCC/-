import csv
import datetime
import io
import logging
import re
import urllib.parse
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user, get_current_user, get_db, get_teacher_user, get_user_by_token
from app.core.config import settings
from app.core.permission import get_allowed_device_ids, require_can_access_device_history
from app.db.models import Class, ClassDeviceBind, Device, GrowthRecord, PlantProfile, SensorReading, User
from app.db.session import SessionLocal
from app.schemas.telemetry import (
    AIScienceAskRequest,
    AIScienceAskResponse,
    ControlRequest,
    DemoScenarioRequest,
    DeviceCreateRequest,
    DeviceResponse,
    ExportRequest,
    TelemetryData,
    TelemetryResponse,
)
from app.services.ai_science_service import ask_qwen_science_assistant
from app.services.telemetry_hub_service import TelemetryHub


router = APIRouter()
telemetry_hub = TelemetryHub()


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
                    "light_state": device.light_state,
                },
            },
        )

        return {
            "status": "success",
            "id": new_reading.id,
            "commands": {
                "pump": device.pump_state,
                "fan": device.fan_state,
                "light": device.light_state,
            },
        }
    except OperationalError:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="遥测数据处理失败，请检查上报格式")


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
        light_state=device_data.light_state,
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
    if data.light_state is not None:
        device.light_state = data.light_state

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
                "light_state": device.light_state,
            },
        },
    )

    return {"status": "success", "device_id": device_id}


@router.post("/api/demo/scenario/{device_id}")
async def trigger_demo_scenario(
    device_id: int,
    request: DemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    scenario_map = {
        "drought": {
            "temp": 32.0,
            "humidity": 38.0,
            "soil_moisture": 12.0,
            "light": 8200.0,
            "pump_state": 0,
            "fan_state": 1,
            "light_state": 1,
            "message": "已切换到干旱场景：土壤湿度偏低，适合讲解蒸腾作用。",
        },
        "heatwave": {
            "temp": 39.0,
            "humidity": 35.0,
            "soil_moisture": 30.0,
            "light": 9000.0,
            "pump_state": 0,
            "fan_state": 1,
            "light_state": 0,
            "message": "已切换到高温场景：建议观察高温对植物气孔调节的影响。",
        },
        "low_light": {
            "temp": 23.0,
            "humidity": 62.0,
            "soil_moisture": 45.0,
            "light": 900.0,
            "pump_state": 0,
            "fan_state": 0,
            "light_state": 1,
            "message": "已切换到低光场景：可引导学生讨论光合作用效率变化。",
        },
        "healthy": {
            "temp": 25.5,
            "humidity": 58.0,
            "soil_moisture": 52.0,
            "light": 5600.0,
            "pump_state": 0,
            "fan_state": 0,
            "light_state": 1,
            "message": "已切换到健康场景：环境稳定，适合安排长期观察记录。",
        },
    }

    payload = scenario_map[request.scenario]

    new_reading = SensorReading(
        device_id=device_id,
        temp=payload["temp"],
        humidity=payload["humidity"],
        soil_moisture=payload["soil_moisture"],
        light=payload["light"],
    )
    db.add(new_reading)

    device.pump_state = payload["pump_state"]
    device.fan_state = payload["fan_state"]
    device.light_state = payload["light_state"]
    device.last_seen = datetime.datetime.utcnow()
    device.status = 1

    db.commit()
    db.refresh(new_reading)
    db.refresh(device)

    await telemetry_hub.broadcast(
        device_id,
        {
            "type": "telemetry_update",
            "device_id": device_id,
            "timestamp": new_reading.timestamp.isoformat() if new_reading.timestamp else None,
            "telemetry": {
                "temp": float(new_reading.temp),
                "humidity": float(new_reading.humidity),
                "soil_moisture": float(new_reading.soil_moisture),
                "light": float(new_reading.light),
            },
            "actuators": {
                "pump_state": device.pump_state,
                "fan_state": device.fan_state,
                "light_state": device.light_state,
            },
        },
    )

    return {
        "status": "success",
        "scenario": request.scenario,
        "message": payload["message"],
    }


@router.post("/api/ai/science-assistant", response_model=AIScienceAskResponse)
async def ask_ai_science_assistant(
    request: AIScienceAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = None
    if request.device_id:
        latest = db.query(SensorReading).filter(SensorReading.device_id == request.device_id).order_by(desc(SensorReading.timestamp)).first()
    else:
        class_ids: List[int] = []
        if current_user.role == "student" and current_user.class_id:
            class_ids = [current_user.class_id]
        elif current_user.role == "teacher":
            class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == current_user.id).all()]

        if class_ids:
            bind = (
                db.query(ClassDeviceBind)
                .filter(ClassDeviceBind.class_id.in_(class_ids))
                .order_by(desc(ClassDeviceBind.id))
                .first()
            )
            if bind:
                latest = (
                    db.query(SensorReading)
                    .filter(SensorReading.device_id == bind.device_id)
                    .order_by(desc(SensorReading.timestamp))
                    .first()
                )

    answer, source = ask_qwen_science_assistant(request.question, latest)
    return AIScienceAskResponse(answer=answer, source=source)


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
                    "light_state": device.light_state if device else 0,
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
        },
        "telemetry": {
            "temp": float(latest_reading.temp) if latest_reading and latest_reading.temp else None,
            "humidity": float(latest_reading.humidity) if latest_reading and latest_reading.humidity else None,
            "soil_moisture": float(latest_reading.soil_moisture) if latest_reading and latest_reading.soil_moisture else None,
            "light": float(latest_reading.light) if latest_reading and latest_reading.light else None,
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
