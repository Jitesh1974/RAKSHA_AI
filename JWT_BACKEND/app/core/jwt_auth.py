"""JWT creation and verification for device authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


class JWTConfigurationError(RuntimeError):
    """Raised when required JWT configuration is missing or invalid."""


def _validate_configuration() -> None:
    if not settings.jwt_secret_key:
        raise JWTConfigurationError("JWT_SECRET_KEY is not configured")

    if len(settings.jwt_secret_key) < 32:
        raise JWTConfigurationError(
            "JWT_SECRET_KEY must contain at least 32 characters"
        )

    if settings.jwt_algorithm != "HS256":
        raise JWTConfigurationError(
            "Only HS256 is supported by the current device-token implementation"
        )

    if settings.jwt_access_token_expire_minutes <= 0:
        raise JWTConfigurationError(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero"
        )


def create_access_token(device_id: str) -> str:
    """Create a signed JWT for a registered device."""
    _validate_configuration()

    normalized_device_id = device_id.strip()
    if not normalized_device_id:
        raise ValueError("device_id is required")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": normalized_device_id,
        "jti": str(uuid4()),
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify a device JWT and return its claims."""
    _validate_configuration()

    if not token or not token.strip():
        raise InvalidTokenError("Empty access token")

    payload = jwt.decode(
        token.strip(),
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={
            "require": [
                "sub",
                "jti",
                "iat",
                "nbf",
                "exp",
                "iss",
                "aud",
                "token_type",
            ]
        },
    )

    if payload.get("token_type") != "access":
        raise InvalidTokenError("Invalid token type")

    device_id = payload.get("sub")
    if not isinstance(device_id, str) or not device_id.strip():
        raise InvalidTokenError("Invalid token subject")

    return payload
