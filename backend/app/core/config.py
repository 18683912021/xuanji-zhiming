from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://xuanji:dev-only@127.0.0.1:5432/xuanji"
    environment: str = "development"
    web_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    cookie_secure: bool = False
    session_days: int = Field(default=14, ge=1, le=30)
    db_pool_size: int = Field(default=4, ge=1, le=12)
    development_admin_password: SecretStr | None = None

    auth_code_secret: SecretStr | None = None
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_sender: str = ""
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_security: Literal["starttls", "tls", "plain"] = "starttls"
    wechat_app_id: str = "wx99173f0f5cf30a60"
    wechat_app_secret: SecretStr | None = None

    ai_provider: Literal["openai", "deepseek"] = "openai"
    ai_base_url: str | None = None
    ai_api_key: SecretStr | None = None
    ai_model: str = ""
    ai_embedding_model: str = ""
    ai_timeout_seconds: int = Field(default=35, ge=5, le=90)
    ai_max_concurrent: int = Field(default=2, ge=1, le=4)

    @property
    def development_admin_enabled(self) -> bool:
        password = self.development_admin_password
        return (
            self.environment == "development"
            and password is not None
            and MIN_PASSWORD_LENGTH <= len(password.get_secret_value()) <= MAX_PASSWORD_LENGTH
        )

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_model and self.ai_api_key and self.ai_api_key.get_secret_value())

    @property
    def email_codes_enabled(self) -> bool:
        return bool(
            self.smtp_host
            and self.smtp_sender
            and self.auth_code_secret
            and len(self.auth_code_secret.get_secret_value()) >= 32
            and (not self.smtp_username or self.smtp_password)
        )

    @property
    def wechat_login_enabled(self) -> bool:
        return bool(
            self.wechat_app_id
            and self.wechat_app_secret
            and self.wechat_app_secret.get_secret_value()
        )

    @property
    def model_base_url(self) -> str:
        if self.ai_base_url:
            return self.ai_base_url
        if self.ai_provider == "deepseek":
            return "https://api.deepseek.com"
        return "https://api.openai.com/v1"

    @model_validator(mode="after")
    def require_secure_production(self) -> "Settings":
        if self.environment == "production":
            if not self.cookie_secure:
                raise ValueError("Production requires Secure session cookies.")
            if any(not origin.startswith("https://") for origin in self.web_origins):
                raise ValueError("Production origins must use HTTPS.")
            if self.smtp_host and self.smtp_security == "plain":
                raise ValueError("Production SMTP requires TLS.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
