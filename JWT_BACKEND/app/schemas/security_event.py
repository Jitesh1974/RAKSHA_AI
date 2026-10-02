from typing import Any

from pydantic import BaseModel, Field, field_validator


class SecurityEvent(BaseModel):
    event_id: str = Field(min_length=8, max_length=128)
    device_id: str | None = Field(default=None, max_length=128)
    source_app: str = Field(min_length=1, max_length=128)
    sender: str | None = Field(default=None, max_length=512)
    message_text: str = Field(default="", max_length=12000)
    urls: list[str] = Field(default_factory=list, max_length=20)
    attachments: list[str] = Field(default_factory=list, max_length=50)
    timestamp: str = Field(min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("urls", "attachments")
    @classmethod
    def cap_items(cls, value: list[str]) -> list[str]:
        return [str(item)[:2048] for item in value[:50]]
