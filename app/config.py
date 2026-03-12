from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "agent-api-stack"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    http_timeout_seconds: int = 15
    http_max_response_bytes: int = 2_000_000
    http_user_agent: str = "JarvisAgentAPI/0.1"

    structured_web_max_html_chars: int = 500_000
    structured_web_max_links: int = 100

    cors_allow_origins: str = ""
    request_max_body_bytes: int = 1_000_000
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    enable_metering: bool = True
    enable_payment_enforcement: bool = False
    payment_shadow_mode: bool = True
    payment_verifier: str = "stub"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
