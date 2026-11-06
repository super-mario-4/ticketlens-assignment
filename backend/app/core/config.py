from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Application settings, read from environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ticketlens"
    postgres_password: SecretStr
    postgres_db: str = "ticketlens"

    elasticsearch_url: str = "http://elasticsearch:9200"
    health_check_timeout_seconds: float = 2.0

    max_import_bytes: int = 10 * 1024 * 1024
    max_ticket_text_length: int = 4000
    import_batch_size: int = 200

    routing_config_path: str = "config/routing.yaml"
    classification_confidence_threshold: float = 0.7
    classifier_retry_delay_seconds: float = 2.0
    processing_timeout_seconds: int = 300

    llm_base_url: str = "http://llm:11434/v1"
    llm_model: str = "qwen3.6:35b-a3b"
    llm_timeout: float = 60.0
    llm_max_tokens: int = 300
    llm_reasoning_effort: str = "none"

    worker_concurrency: int = 3
    worker_poll_seconds: float = 5.0

    search_index: str = "tickets"
    search_timeout_seconds: float = 5.0
    search_max_hits: int = 1000
    outbox_batch_size: int = 200
    outbox_poll_seconds: float = 5.0

    retention_days: int = 90
    retention_check_seconds: int = 24 * 60 * 60

    # Demo values for local use only (TRD section 8).
    jwt_secret: SecretStr = SecretStr("ticketlens-local-demo-secret-not-for-production")
    jwt_expire_minutes: int = 480
    operator_username: str = "operator"
    operator_password: SecretStr = SecretStr("operator")
    lead_username: str = "lead"
    lead_password: SecretStr = SecretStr("lead")

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
