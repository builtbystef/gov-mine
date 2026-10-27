from datetime import timedelta

from pydantic import Field, HttpUrl, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from gov_mine.integrations.ai import AIProvider, ReasoningEffort
from gov_mine.integrations.storage import StorageProvider
from gov_mine.shared.logs import LogFormat


class Settings(BaseSettings):
    """Read from `GOV_MINE_*` environment variables and `.env`. `.env.example` documents
    every field.

    Built once per process by its entry point (asgi.py, the CLI, a script) and
    passed on from there; nothing reads the environment at import time. Tests build
    their own."""

    # --- App ---
    app_name: str = "gov-mine API"
    log_level: str = "INFO"
    # "text" for a terminal, "json" for a log collector.
    log_format: LogFormat = "text"
    # Logfire write token. None: telemetry is off.
    logfire_token: SecretStr | None = None
    # Shown in Logfire to tell deployments apart.
    logfire_environment: str = "development"

    # --- Database ---
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://gov_mine:gov_mine@localhost:5432/gov_mine"
    )
    database_echo: bool = False
    database_pool_size: int = Field(5, ge=1)
    database_max_overflow: int = Field(10, ge=0)
    # PostgreSQL cancels any statement that runs longer than this.
    database_statement_timeout: timedelta = timedelta(seconds=30)

    # --- Object storage ---
    # "s3" covers every S3-compatible service.
    storage_provider: StorageProvider = "s3"
    storage_bucket: str = "gov-mine"
    # None for AWS S3 itself.
    storage_endpoint_url: HttpUrl | None = HttpUrl("http://127.0.0.1:9000")
    # Where the browser reaches storage, when that differs from the endpoint above.
    storage_public_endpoint_url: HttpUrl | None = None
    storage_region: str = "us-east-1"
    storage_access_key: str = "rustfsadmin"
    storage_secret_key: SecretStr = SecretStr("rustfsadmin")
    # True: host/bucket/key URLs (RustFS, MinIO). False: bucket.host/key (AWS).
    storage_path_style: bool = True
    storage_url_ttl: timedelta = timedelta(minutes=15)

    # --- Background jobs ---
    # Jobs one worker process runs at a time.
    jobs_concurrency: int = Field(2, ge=1)

    # --- AI ---
    # "openai" addresses the model through the Responses API.
    ai_provider: AIProvider = "openai"
    # None: nothing calls the model.
    openai_api_key: SecretStr | None = None
    ai_model: str = "gpt-5.6-luna"
    ai_reasoning_effort: ReasoningEffort = "low"

    # env_ignore_empty: hosting platforms often pass an unset variable as "",
    # which must read as the default (None for the Logfire token), not as "".
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="GOV_MINE_", env_ignore_empty=True
    )
