from __future__ import annotations

import os
from dataclasses import dataclass


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_int(name: str, default: int) -> int:
    value = env(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    environment: str = env("ENVIRONMENT", "development")
    host: str = env("HOST", "0.0.0.0")
    port: int = int(env("PORT", "8000"))
    database_url: str = env("DATABASE_URL")
    llm_base_url: str = env("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8081/v1")
    public_api_origin: str = env("PUBLIC_API_ORIGIN", "http://localhost:8000")
    device_token_ttl_days: int = int(env("DEVICE_TOKEN_TTL_DAYS", "180"))
    jwt_secret_key: str = env("JWT_SECRET_KEY")
    jwt_algorithm: str = env("JWT_ALGORITHM", "HS256")
    jwt_issuer: str = env("JWT_ISSUER", "raksha-ai")
    jwt_audience: str = env("JWT_AUDIENCE", "raksha-ai-api")
    jwt_access_token_expire_minutes: int = env_int(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        device_token_ttl_days * 24 * 60,
    )


settings = Settings()
