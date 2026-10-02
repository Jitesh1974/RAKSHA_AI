from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_auth import create_access_token
from app.db.models import AnalysisRecord, Device, SecurityEventRecord
from app.schemas.risk_report import EvidenceItem, RiskReport
from app.schemas.security_event import SecurityEvent


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def register_or_refresh_device(
    session: AsyncSession,
    *,
    device_id: str,
    app_version: str | None,
) -> tuple[str, Device]:
    token = create_access_token(device_id)
    now = utcnow()
    result = await session.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        device = Device(
            device_id=device_id,
            token_hash=hash_token(token),
            app_version=app_version,
            created_at=now,
            last_seen_at=now,
        )
        session.add(device)
    else:
        device.token_hash = hash_token(token)
        device.app_version = app_version or device.app_version
        device.last_seen_at = now
        device.revoked_at = None
    await session.commit()
    await session.refresh(device)
    return token, device


async def authenticate_device(session: AsyncSession, *, token: str, device_id: str) -> Device | None:
    result = await session.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.token_hash == hash_token(token),
        )
    )
    device = result.scalar_one_or_none()
    if device is None or device.revoked_at is not None:
        return None
    device.last_seen_at = utcnow()
    await session.commit()
    return device


async def save_event(session: AsyncSession, event: SecurityEvent, device_id: str) -> None:
    record = SecurityEventRecord(
        event_id=event.event_id,
        device_id=device_id,
        source_app=event.source_app,
        sender=event.sender,
        message_text=event.message_text,
        urls=event.urls,
        attachments=event.attachments,
        metadata_json=event.metadata,
        event_timestamp=event.timestamp,
    )
    await session.merge(record)
    await session.commit()


async def get_analysis(session: AsyncSession, event_id: str) -> RiskReport | None:
    result = await session.execute(select(AnalysisRecord).where(AnalysisRecord.event_id == event_id))
    record = result.scalar_one_or_none()
    if record is None:
        return None

    evidence = [EvidenceItem.model_validate(item) for item in (record.evidence or [])]
    return RiskReport(
        risk_score=record.risk_score,
        risk_level=record.risk_level,
        scam_category=record.scam_category,
        explanation=record.explanation,
        recommended_action=record.recommended_action,
        evidence=evidence,
    )


async def save_analysis(session: AsyncSession, event_id: str, report: RiskReport) -> None:
    record = AnalysisRecord(
        id=str(uuid.uuid4()),
        event_id=event_id,
        risk_score=report.risk_score,
        risk_level=report.risk_level,
        scam_category=report.scam_category,
        explanation=report.explanation,
        recommended_action=report.recommended_action,
        evidence=[item.model_dump() for item in report.evidence],
    )
    await session.merge(record)
    await session.commit()
