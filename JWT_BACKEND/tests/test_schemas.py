import pytest
from pydantic import ValidationError

from app.schemas.risk_report import EvidenceItem, RiskReport
from app.schemas.security_event import SecurityEvent


def test_security_event_rejects_oversized_collections():
    with pytest.raises(ValidationError):
        SecurityEvent(
            event_id="event-123456",
            source_app="com.whatsapp",
            message_text="hello",
            timestamp="2026-10-01T10:00:00Z",
            urls=["https://example.com" for _ in range(21)],
        )

    with pytest.raises(ValidationError):
        SecurityEvent(
            event_id="event-123456",
            source_app="com.whatsapp",
            message_text="hello",
            timestamp="2026-10-01T10:00:00Z",
            attachments=["bad.apk" for _ in range(51)],
        )


def test_security_event_bounded_items():
    long_url = "https://example.com/" + ("a" * 3000)
    event = SecurityEvent(
        event_id="event-123456",
        source_app="com.whatsapp",
        message_text="hello",
        timestamp="2026-10-01T10:00:00Z",
        urls=[long_url],
    )
    assert len(event.urls[0]) == 2048


def test_risk_report_accepts_structured_evidence():
    report = RiskReport(
        risk_score=82,
        risk_level="high",
        scam_category="phishing",
        explanation="Suspicious link and urgency language detected.",
        recommended_action="Do not open the link.",
        evidence=[
            EvidenceItem(
                type="url",
                signal="reputation",
                weight=30,
                detail="Domain reputation issue",
            )
        ],
    )
    assert report.evidence[0].signal == "reputation"
