from __future__ import annotations

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(v: Optional[str]) -> List[str]:
    if not v:
        return []
    return [item.strip() for item in v.split(",") if item.strip()]


class Settings(BaseSettings):
    # -------------------- App --------------------
    title: str = "Bank Simulator with Digital Twin"
    version: str = "0.1.0"

    # -------------------- DB ---------------------
    database_url: Optional[str] = None
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30

    # -------------------- Auth / JWT -------------
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # -------------------- MQTT -------------------
    mqtt_broker_host: str = "mqtt-broker"
    mqtt_broker_port: int = 1883

    # -------------------- CORS -------------------
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    # -------------------- Front ------------------
    react_app_api_url: str = "http://localhost:8000"

    # -------------------- Pydantic config --------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        extra="ignore",  # ignora variáveis de ambiente não mapeadas
    )

    def model_post_init(self, __context: dict) -> None:
        # Permitir CORS_ORIGINS em CSV
        if isinstance(self.cors_origins, str):
            self.cors_origins = _split_csv(self.cors_origins)

    def require_api_fields(self) -> None:
        if not self.database_url:
            raise ValueError("DATABASE_URL não definido no .env")
        if not self.secret_key:
            raise ValueError("SECRET_KEY não definido no .env")
