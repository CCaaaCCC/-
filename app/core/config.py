import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://greenhouse_user:change_this_password_in_production@localhost:3306/smart_greenhouse",
    )
    secret_key: str = _require_env("SECRET_KEY")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    device_token: str = os.getenv("DEVICE_TOKEN", "default_secret_device_token")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    cors_origins: list[str] = None  # type: ignore[assignment]
    seed_demo_data: bool = os.getenv("SEED_DEMO_DATA", "false").lower() in ("1", "true", "yes", "y", "on")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cors_origins",
            _parse_cors_origins(os.getenv("CORS_ORIGINS")),
        )


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


settings = Settings()

