import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "y", "on")


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

    # DeepSeek API configuration.
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    ai_langchain_enabled: bool = _as_bool(os.getenv("AI_LANGCHAIN_ENABLED"), default=True)
    ai_stream_enabled: bool = _as_bool(os.getenv("AI_STREAM_ENABLED"), default=True)
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.4"))
    ai_timeout_seconds: int = int(os.getenv("AI_TIMEOUT_SECONDS", "20"))
    ai_stream_timeout_seconds: int = int(os.getenv("AI_STREAM_TIMEOUT_SECONDS", "45"))
    ai_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "600"))
    ai_retry_count: int = int(os.getenv("AI_RETRY_COUNT", "1"))
    ai_retry_backoff_ms: int = int(os.getenv("AI_RETRY_BACKOFF_MS", "300"))
    ai_chat_model: str = os.getenv("AI_CHAT_MODEL", os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")).strip()
    ai_reasoner_model: str = os.getenv(
        "AI_REASONER_MODEL",
        os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-reasoner"),
    ).strip()

    rag_enabled: bool = _as_bool(os.getenv("RAG_ENABLED"), default=True)
    rag_index_dir: str = os.getenv("RAG_INDEX_DIR", "data/chroma")
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))

    cors_origins: list[str] = None  # type: ignore[assignment]
    cors_origin_regex: str | None = None
    seed_demo_data: bool = _as_bool(os.getenv("SEED_DEMO_DATA"), default=False)

    def __post_init__(self) -> None:
        raw_cors_origins = os.getenv("CORS_ORIGINS")
        raw_cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX")
        object.__setattr__(
            self,
            "cors_origins",
            _parse_cors_origins(raw_cors_origins),
        )
        object.__setattr__(
            self,
            "cors_origin_regex",
            _parse_cors_origin_regex(raw_cors_origins, raw_cors_origin_regex),
        )


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def _parse_cors_origin_regex(cors_origins_raw: str | None, regex_raw: str | None) -> str | None:
    if regex_raw is not None:
        normalized = regex_raw.strip()
        return normalized or None

    if cors_origins_raw and cors_origins_raw.strip():
        return None

    # Default allows localhost plus private LAN ranges for classroom/demo access.
    return r"^https?://(localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(:\d+)?$"


settings = Settings()

