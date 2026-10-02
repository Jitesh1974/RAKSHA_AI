"""Authentication endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import register_or_refresh_device
from app.db.session import get_session
from app.schemas.auth import DeviceRegistrationRequest, DeviceRegistrationResponse
from app.services.google_auth import exchange_code, get_authorization_url
from app.services.token_store import TokenStore

logger = logging.getLogger(__name__)

device_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
legacy_google_router = APIRouter(prefix="/api/v1/auth", tags=["Legacy Google OAuth"])


@device_router.post("/device/register", response_model=DeviceRegistrationResponse)
async def register_device(
    payload: DeviceRegistrationRequest,
    session: AsyncSession = Depends(get_session),
):
    # First-install bootstrap. Before public launch this endpoint should be
    # protected by device attestation, abuse controls, and account lifecycle rules.
    token, _ = await register_or_refresh_device(
        session, device_id=payload.device_id, app_version=payload.app_version
    )
    return DeviceRegistrationResponse(device_id=payload.device_id, access_token=token)


class ExchangeRequest(BaseModel):
    auth_code: str = Field(..., min_length=4)


@legacy_google_router.get("/google/login", summary="Legacy browser OAuth")
def login():
    try:
        auth_url, _ = get_authorization_url()
        return RedirectResponse(url=auth_url)
    except ValueError as err:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured") from err


@legacy_google_router.get("/google/callback", summary="Legacy browser OAuth callback")
def callback(code: str = Query(...), state: str | None = Query(None)):
    try:
        user_email, refresh_token = exchange_code(code)
        TokenStore.save_refresh_token(user_email, refresh_token)
        return {"connected": user_email}
    except Exception as err:
        logger.warning("legacy_google_callback_failed error_type=%s", type(err).__name__)
        raise HTTPException(status_code=400, detail="OAuth callback failed") from err


@legacy_google_router.post("/google/exchange", summary="Legacy Android Server Auth Code Exchange")
def exchange_android_code(payload: ExchangeRequest):
    try:
        user_email, refresh_token = exchange_code(payload.auth_code, redirect_uri="")
        TokenStore.save_refresh_token(user_email, refresh_token)
        return {"connected": user_email}
    except Exception as err:
        logger.warning("legacy_google_exchange_failed error_type=%s", type(err).__name__)
        raise HTTPException(status_code=400, detail="Android token exchange failed") from err
