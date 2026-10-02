"""RAKSHA AI production API entry point."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from app.api.auth import device_router, legacy_google_router
from app.api.email import router as email_router
from app.api.events import router as events_router
from app.core.logging import configure_logging
from app.db.session import check_database
from app.llm.llama_cpp import check_health as check_llama_health
from app.services.analysis_control import configured_fallback_provider, configured_provider

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAKSHA AI API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(events_router)
app.include_router(device_router)

# Legacy integrations are opt-in and excluded from normal production deployments.
if os.getenv("ENABLE_LEGACY_GOOGLE_AUTH", "false").strip().lower() == "true":
    app.include_router(legacy_google_router)
if os.getenv("ENABLE_LEGACY_EMAIL_SYNC", "false").strip().lower() == "true":
    app.include_router(email_router)


@app.get("/health/live", tags=["Health"])
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
async def health_ready() -> dict[str, object]:
    db_ok = await check_database()
    llama = check_llama_health()
    llama_ok = llama.get("status") == "ok"
    return {
        "status": "ok" if db_ok and llama_ok else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "llm": llama,
    }


@app.get("/health", include_in_schema=False)
async def health_alias() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/llm", tags=["Health"])
def llm_health_check() -> dict[str, object]:
    message_provider = configured_provider("message_agent")
    explanation_provider = configured_provider("explanation_agent")
    result: dict[str, object] = {
        "message_agent_provider": message_provider,
        "explanation_agent_provider": explanation_provider,
        "fallback_provider_message_agent": configured_fallback_provider("message_agent"),
        "fallback_provider_explanation_agent": configured_fallback_provider("explanation_agent"),
    }
    local_providers = {"llama_cpp", "llama.cpp", "local"}
    if message_provider in local_providers or explanation_provider in local_providers:
        result["llama_cpp"] = check_llama_health()
    else:
        result["llama_cpp"] = {"status": "not_configured"}
    return result
