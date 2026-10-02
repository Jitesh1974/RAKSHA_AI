"""Versioned security event analysis API."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import workflow
from app.api.deps import current_device
from app.db.models import Device
from app.db.neo4j import upsert_event_graph
from app.db.repositories import get_analysis, save_analysis, save_event
from app.db.session import get_session
from app.schemas.risk_report import RiskReport
from app.schemas.security_event import SecurityEvent
from app.services.analysis_control import AnalysisUnavailable, get_controller

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/events", tags=["Security Events"])


@router.post("/analyze", response_model=RiskReport)
async def analyze_security_event(
    event: SecurityEvent,
    device: Device = Depends(current_device),
    session: AsyncSession = Depends(get_session),
) -> RiskReport:
    if event.device_id and event.device_id != device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device mismatch")

    normalized = event.model_copy(update={"device_id": device.device_id})
    request_id = uuid.uuid4().hex
    logger.info(
        "event_received request_id=%s event_id=%s device_id=%s",
        request_id,
        normalized.event_id,
        device.device_id,
    )

    # Idempotency: notification listeners can deliver the same event more than once.
    existing = await get_analysis(session, normalized.event_id)
    if existing is not None:
        return existing

    try:
        await save_event(session, normalized, device.device_id)
        with get_controller().analysis_slot(request_id):
            result = await workflow.ainvoke({"event": normalized, "request_id": request_id})
    except AnalysisUnavailable as exc:
        logger.warning("analysis_unavailable request_id=%s event_id=%s", request_id, normalized.event_id)
        raise HTTPException(status_code=503, detail="Analysis is temporarily unavailable") from exc
    except Exception as exc:
        logger.exception("event_analysis_failed request_id=%s event_id=%s", request_id, normalized.event_id)
        raise HTTPException(status_code=500, detail="Security event analysis failed") from exc

    risk_report = result.get("risk_report")
    if risk_report is None:
        raise HTTPException(status_code=500, detail="Workflow did not produce a risk report")
    if not isinstance(risk_report, RiskReport):
        risk_report = RiskReport.model_validate(risk_report)

    try:
        await save_analysis(session, normalized.event_id, risk_report)
    except Exception:
        logger.exception("analysis_persistence_failed event_id=%s", normalized.event_id)

    try:
        await upsert_event_graph(
            event_id=normalized.event_id,
            device_id=device.device_id,
            sender=normalized.sender,
            urls=normalized.urls,
        )
    except Exception:
        # Graph analytics are supplementary; a graph outage must not turn a completed
        # security analysis into an API failure.
        logger.exception("neo4j_upsert_failed event_id=%s", normalized.event_id)

    return risk_report
