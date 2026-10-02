from typing import Any

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    type: str = "unknown"
    signal: str = "unknown"
    weight: float = 0.0
    detail: str = ""
    url: str | None = None
    filename: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskReport(BaseModel):
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    scam_category: str
    explanation: str
    recommended_action: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
