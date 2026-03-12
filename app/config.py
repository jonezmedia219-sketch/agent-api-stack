from functools import lru_cache

from pydantic import AliasChoices, Field
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
    payment_chain: str = "base"
    payment_token: str = "USDC"
    payment_receiver_wallet: str = Field(
        default="0xa850773dDdAc7051c9434E3b1e804531C12d265c",
        validation_alias=AliasChoices("PAYMENT_RECEIVER_WALLET", "PAYMENT_RECEIVER_WALET"),
    )
    payment_max_skew_seconds: int = 300
    payment_require_nonce: bool = True
    payment_shared_secret: str = "change-me-before-production"
    base_rpc_url: str = "https://mainnet.base.org"
    payment_token_contract: str = "0x833589fCD6EDB6E08f4c7C32D4f71b54bdA02913"
    payment_min_confirmations: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
