"""Legacy Gmail integration placeholder.

The original prototype stored refresh tokens outside the application database and
ran email analysis without device-scoped authorization. That path is deliberately
not enabled in the production API. The module remains available behind an explicit
environment flag while the user-scoped Gmail flow is migrated.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/email", tags=["Legacy Email"])


class EmailSyncRequest(BaseModel):
    user_email: str


@router.post("/sync")
async def sync_emails(_: EmailSyncRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Gmail synchronization is disabled in the production API until user-scoped OAuth storage is migrated.",
    )
