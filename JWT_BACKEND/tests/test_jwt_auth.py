import os

import jwt
import pytest


# These unit tests set the JWT environment before importing the module so the
# test suite does not require a production .env file.
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-change-me-abcdefghijklmnopqrstuvwxyz-123456")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ISSUER", "raksha-ai")
os.environ.setdefault("JWT_AUDIENCE", "raksha-ai-api")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.core.config import settings  # noqa: E402
from app.core.jwt_auth import create_access_token, decode_access_token  # noqa: E402


def test_jwt_round_trip():
    token = create_access_token("test-device-123")
    claims = decode_access_token(token)

    assert claims["sub"] == "test-device-123"
    assert claims["token_type"] == "access"
    assert claims["iss"] == settings.jwt_issuer
    assert claims["aud"] == settings.jwt_audience
    assert claims["jti"]


def test_jwt_rejects_tampering():
    token = create_access_token("test-device-123")
    header, payload, signature = token.split(".")
    tampered_payload = jwt.utils.base64url_encode(b'{"sub":"other-device"}').decode()
    tampered = f"{header}.{tampered_payload}.{signature}"

    with pytest.raises(jwt.exceptions.InvalidTokenError):
        decode_access_token(tampered)
