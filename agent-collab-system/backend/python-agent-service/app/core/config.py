import json
import os
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
from typing import cast


def _load_local_env_files() -> None:
    service_root = Path(__file__).resolve().parents[2]
    for candidate in (service_root / '.env.local', service_root / '.env'):
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            normalized = value.strip().strip('"').strip("'")
            os.environ[key] = normalized


_load_local_env_files()


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

    mock_pghost: str = os.getenv("MOCK_PGHOST", os.getenv("PGHOST", "localhost"))
    mock_pgport: int = _get_int("MOCK_PGPORT", _get_int("PGPORT", 55432))
    mock_pguser: str = os.getenv("MOCK_PGUSER", os.getenv("PGUSER", "postgres"))
    mock_pgpassword: str = os.getenv("MOCK_PGPASSWORD", os.getenv("PGPASSWORD", "postgres"))
    mock_pgdatabase: str = os.getenv("MOCK_PGDATABASE", "dayan_mock_records")

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = _get_int("REDIS_PORT", 56379)
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = _get_int("REDIS_DB", 0)

    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:59000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket: str = os.getenv("S3_BUCKET", "dayan-agent-files")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

    default_llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini_proxy")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-3-flash-preview-thinking")
    llm_request_path: str = os.getenv("LLM_REQUEST_PATH", "/chat/completions")
    llm_timeout_ms: int = _get_int("LLM_TIMEOUT_MS", 30000)
    allow_header_auth_fallback: bool = os.getenv("ALLOW_HEADER_AUTH_FALLBACK", "false").lower() == "true"
    gemini_proxy_api_key: str = os.getenv("GEMINI_PROXY_API_KEY", "")
    gemini_proxy_base_url: str = os.getenv("GEMINI_PROXY_BASE_URL", "")
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
    go_records_base_url: str = os.getenv("GO_RECORDS_BASE_URL", "")
    go_records_timeout_ms: int = _get_int("GO_RECORDS_TIMEOUT_MS", 8000)
    runtime_default_tenant_id: str = os.getenv("RUNTIME_DEFAULT_TENANT_ID", "tenant_local")
    enable_mock_records_gateway: bool = _get_bool("ENABLE_MOCK_RECORDS_GATEWAY", True)
    department_table_route_map_json: str = os.getenv("DEPARTMENT_TABLE_ROUTE_MAP_JSON", "{}")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )

    @property
    def mock_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.mock_pguser}:{self.mock_pgpassword}"
            f"@{self.mock_pghost}:{self.mock_pgport}/{self.mock_pgdatabase}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def department_table_route_map(self) -> dict[str, dict[str, str]]:
        try:
            data = cast(object, json.loads(self.department_table_route_map_json))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        normalized: dict[str, dict[str, str]] = {}
        raw_items = cast(dict[object, object], data)
        for target_code, config in raw_items.items():
            if not isinstance(target_code, str) or not isinstance(config, dict):
                continue
            normalized[target_code] = {
                key: str(value)
                for key, value in cast(dict[object, object], config).items()
                if isinstance(key, str) and value is not None
            }
        return normalized

    @property
    def resolved_llm_api_key(self) -> str:
        if self.llm_api_key:
            return self.llm_api_key
        if self.default_llm_provider == "gemini_proxy" and self.gemini_proxy_api_key:
            return self.gemini_proxy_api_key
        if self.default_llm_provider == "deepseek":
            return self.deepseek_api_key
        return ""

    @property
    def resolved_llm_base_url(self) -> str:
        if self.llm_base_url:
            return self.llm_base_url.rstrip("/")
        if self.default_llm_provider == "gemini_proxy" and self.gemini_proxy_base_url:
            return self.gemini_proxy_base_url.rstrip("/")
        if self.default_llm_provider == "deepseek" and self.deepseek_base_url:
            return self.deepseek_base_url.rstrip("/")
        return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
