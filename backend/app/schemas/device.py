from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class DeviceCreate(BaseModel):
    mac_address: str
    ip_address: str | None = None
    hostname: str | None = None
    vendor: str | None = None
    device_type: str | None = None

    @field_validator("mac_address")
    @classmethod
    def normalize_mac_address(cls, value: str) -> str:
        value = value.strip().replace("-", ":").upper()

        parts = value.split(":")

        if len(parts) != 6 or any(
            len(part) != 2 or not all(char in "0123456789ABCDEF" for char in part)
            for part in parts
        ):
            raise ValueError("Invalid MAC address format.")

        return ":".join(parts)

class DeviceUpdate(BaseModel):
    ip_address: str | None = None
    hostname: str | None = None
    vendor: str | None = None
    device_type: str | None = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mac_address: str
    ip_address: str | None
    hostname: str | None
    vendor: str | None
    device_type: str | None
    first_seen: datetime
    last_seen: datetime
