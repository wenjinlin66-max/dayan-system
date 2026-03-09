import os
from dataclasses import dataclass
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "dayan-agent-service")
    app_env: str = os.getenv("APP_ENV", "local")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = _get_int("APP_PORT", 8000)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    pghost: str = os.getenv("PGHOST", "localhost")
    pgport: int = _get_int("PGPORT", 55432)
    pguser: str = os.getenv("PGUSER", "postgres")
    pgpassword: str = os.getenv("PGPASSWORD", "postgres")
    pgdatabase: str = os.getenv("PGDATABASE", "dayan_agentic2")

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = _get_int("REDIS_PORT", 56379)
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = _get_int("REDIS_DB", 0)

    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:59000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket: str = os.getenv("S3_BUCKET", "dayan-agent-files")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

    default_llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BGE-M3")
    rerank_provider: str = os.getenv("RERANK_PROVIDER", "local")
    rerank_model: str = os.getenv("RERANK_MODEL", "BGE-Reranker-v2-m3")
    use_gpu: bool = _get_bool("USE_GPU", True)

    langgraph_version_pin: str = os.getenv("LANGGRAPH_VERSION_PIN", "0.2.56")
    realtime_transport: str = os.getenv("REALTIME_TRANSPORT", "sse")
    workflow_default_mode: str = os.getenv("WORKFLOW_DEFAULT_MODE", "released")
    enable_sandbox_mode: bool = _get_bool("ENABLE_SANDBOX_MODE", True)
    scheduler_enabled: bool = _get_bool("SCHEDULER_ENABLED", True)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
