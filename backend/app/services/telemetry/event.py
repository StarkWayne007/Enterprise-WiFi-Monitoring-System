import ipaddress
import re
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class TelemetryEvent(BaseModel):

    @field_validator("ip_address", "destination_ip")
    @classmethod
    def validate_ip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
 
        value = value.strip()
 
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            raise ValueError("Invalid IP address.")


    @field_validator("device_mac")
    @classmethod
    def validate_device_mac(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().replace("-", ":").upper()

        if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", value):
            raise ValueError("Invalid MAC address format.")

        return value

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: Literal["traffic", "device_seen"]
    source: str
    device_mac: str | None = None
    ip_address: str | None = None
    hostname: str | None = None
    vendor: str | None = None
    device_type: str | None = None
    destination_ip: str | None = None
    protocol: str | None = None
    bytes_transferred: int = Field(default=0, ge=0)
