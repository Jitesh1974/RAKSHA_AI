from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_auth import JWTConfigurationError, decode_access_token
from app.db.models import Device
from app.db.repositories import authenticate_device
from app.db.session import get_session


bearer_scheme = HTTPBearer(auto_error=False)


async def current_device(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_device_id: str | None = Header(default=None, alias="X-Device-ID"),
    session: AsyncSession = Depends(get_session),
) -> Device:
    if credentials is None or not x_device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    device_id = x_device_id.strip()
    if not token or not device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = decode_access_token(token)
    except JWTConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT authentication is not configured",
        ) from exc
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token_device_id = str(claims.get("sub", "")).strip()
    if token_device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    device = await authenticate_device(
        session,
        token=token,
        device_id=device_id,
    )
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return device
