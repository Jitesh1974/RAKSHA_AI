"""Local llama.cpp OpenAI-compatible client for RAKSHA AI.

The model runs outside the FastAPI process (typically on the same Windows PC)
and is exposed through llama.cpp's HTTP server. This keeps model inference out
of the Android APK while preserving the existing agent interface.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LlamaCppUnavailable(RuntimeError):
    """Raised when the local llama.cpp server cannot produce a valid result."""


@dataclass(frozen=True)
class LlamaCppSettings:
    base_url: str
    model: str
    timeout_seconds: float
    max_tokens: int
    temperature: float
    retry_count: int

    @classmethod
    def from_env(cls) -> "LlamaCppSettings":
        base_url = os.getenv("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8081/v1").strip()
        base_url = base_url.rstrip("/")
        if not base_url:
            base_url = "http://127.0.0.1:8081/v1"

        return cls(
            base_url=base_url,
            model=os.getenv("LLAMA_CPP_MODEL", "raksha-qwen").strip() or "raksha-qwen",
            timeout_seconds=_positive_float("LLAMA_CPP_TIMEOUT_SECONDS", 60.0),
            max_tokens=_positive_int("LLAMA_CPP_MAX_TOKENS", 256),
            temperature=_non_negative_float("LLAMA_CPP_TEMPERATURE", 0.1),
            retry_count=_non_negative_int("LLAMA_CPP_RETRY_COUNT", 0),
        )


def _positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def _positive_float(name: str, default: float) -> float:
    try:
        return max(0.1, float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def _non_negative_float(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def _non_negative_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def _message_role(message: Any) -> str:
    role = getattr(message, "type", None)
    if role == "human":
        return "user"
    if role == "ai":
        return "assistant"
    if role == "system":
        return "system"
    if role in {"tool", "function"}:
        return "tool"
    return "user"


def _message_content(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # LangChain can represent multimodal content as a list. RAKSHA's current
        # agents only send text, but flatten text parts safely for compatibility.
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
        return "\n".join(text_parts)
    return str(content)


def serialize_messages(messages: list[Any]) -> list[dict[str, str]]:
    """Convert LangChain-style messages to OpenAI-compatible chat messages."""
    return [
        {
            "role": _message_role(message),
            "content": _message_content(message),
        }
        for message in messages
    ]


def _schema_instruction(schema: type[BaseModel]) -> str:
    schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    return (
        "Return ONLY one valid JSON object. Do not use Markdown fences. "
        "Do not add commentary before or after the JSON. The JSON must conform "
        f"to this JSON Schema: {schema_json}"
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    decoder = json.JSONDecoder()
    start = cleaned.find("{")
    if start < 0:
        raise LlamaCppUnavailable("Model returned no JSON object")

    try:
        payload, _ = decoder.raw_decode(cleaned[start:])
    except json.JSONDecodeError as exc:
        raise LlamaCppUnavailable("Model returned malformed JSON") from exc

    if not isinstance(payload, dict):
        raise LlamaCppUnavailable("Model returned a non-object JSON value")
    return payload


def _completion_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _health_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        base = base_url[:-3].rstrip("/")
    else:
        base = base_url.rstrip("/")
    return f"{base}/health"


def check_health() -> dict[str, Any]:
    """Check llama.cpp server health without sending user data."""
    settings = LlamaCppSettings.from_env()
    try:
        with httpx.Client(timeout=min(settings.timeout_seconds, 5.0)) as client:
            response = client.get(_health_url(settings.base_url))
            response.raise_for_status()
            payload: Any = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("llama.cpp health check failed: error_type=%s", type(exc).__name__)
        return {
            "status": "unavailable",
            "provider": "llama_cpp",
            "model": settings.model,
            "error_type": type(exc).__name__,
        }

    return {
        "status": "ok",
        "provider": "llama_cpp",
        "model": settings.model,
        "server": payload,
    }


def invoke_structured(
    *,
    schema: type[T],
    messages: list[Any],
    temperature: float | None = None,
) -> T:
    """Call llama.cpp and validate the response with the requested Pydantic schema."""
    settings = LlamaCppSettings.from_env()
    request_messages = serialize_messages(messages)
    schema_instruction = _schema_instruction(schema)

    # Keep the output contract in a trusted system message. Event/notification
    # text stays in the user message and therefore cannot override the contract.
    for message in request_messages:
        if message["role"] == "system":
            message["content"] = f'{message["content"]}\n\n{schema_instruction}'
            break
    else:
        request_messages.insert(0, {"role": "system", "content": schema_instruction})

    payload = {
        "model": settings.model,
        "messages": request_messages,
        "temperature": settings.temperature if temperature is None else max(0.0, float(temperature)),
        "max_tokens": settings.max_tokens,
        "stream": False,
        # llama.cpp supports OpenAI-compatible structured output on current
        # releases. The schema is also embedded in the instruction above so
        # older server builds still have a deterministic contract to follow.
        "response_format": {"type": "json_object"},
    }

    last_error: BaseException | None = None
    url = _completion_url(settings.base_url)

    for attempt in range(settings.retry_count + 1):
        try:
            with httpx.Client(timeout=settings.timeout_seconds) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code >= 500:
                    raise LlamaCppUnavailable("llama.cpp server returned a server error")
                response.raise_for_status()
                body = response.json()

            choices = body.get("choices") if isinstance(body, dict) else None
            if not isinstance(choices, list) or not choices:
                raise LlamaCppUnavailable("llama.cpp response contained no choices")

            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str):
                raise LlamaCppUnavailable("llama.cpp response contained no text content")

            parsed = _extract_json_object(content)
            try:
                return schema.model_validate(parsed)
            except ValidationError as exc:
                raise LlamaCppUnavailable("Model JSON did not match the requested schema") from exc
        except Exception as exc:
            last_error = exc
            if attempt < settings.retry_count:
                continue
            logger.warning(
                "llama.cpp request failed: error_type=%s attempts=%s",
                type(exc).__name__,
                attempt + 1,
            )

    raise LlamaCppUnavailable("llama.cpp analysis unavailable after bounded retries") from last_error
