from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.bootstrap import init_demo_data

# --- FastAPI 实例 ---
app = FastAPI(title="智慧大棚后端 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT = "uploads"
PLANT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "plants")
AVATAR_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "avatars")
CONTENT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "content")
MARKET_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "market")
os.makedirs(PLANT_UPLOAD_DIR, exist_ok=True)
os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
os.makedirs(CONTENT_UPLOAD_DIR, exist_ok=True)
os.makedirs(MARKET_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

# --- 初始化数据 ---
@app.on_event("startup")
def startup_event():
    init_demo_data()

@app.get("/")
async def root():
    return {"message": "智慧大棚后端服务运行中..."}


from app.api.routes.auth import router as auth_router
from app.api.routes.assignments import router as assignments_router
from app.api.routes.content import router as content_router
from app.api.routes.users import router as users_router
from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.profile import router as profile_router
from app.api.routes.history import router as history_router
from app.api.routes.plants import router as plants_router
from app.api.routes.groups import router as groups_router
from app.api.routes.logs import router as logs_router
from app.api.routes.market import router as market_router

app.include_router(auth_router)
app.include_router(assignments_router)
app.include_router(content_router)
app.include_router(users_router)
app.include_router(telemetry_router)
app.include_router(profile_router)
app.include_router(history_router)
app.include_router(plants_router)
app.include_router(groups_router)
app.include_router(logs_router)
app.include_router(market_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
