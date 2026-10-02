from pydantic import BaseModel, Field


class DeviceRegistrationRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    app_version: str | None = Field(default=None, max_length=32)


class DeviceRegistrationResponse(BaseModel):
    device_id: str
    access_token: str
    token_type: str = "bearer"
