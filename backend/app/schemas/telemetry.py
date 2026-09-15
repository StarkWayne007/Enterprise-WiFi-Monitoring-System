from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelemetryEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: str
    source: str
    device_mac: str | None
    ip_address: str | None
    destination_ip: str | None
    protocol: str | None
    bytes_transferred: int
    created_at: datetime

class TrafficDataPoint(BaseModel):
    timestamp: datetime
    bytes_transferred: int


class TrafficHistoryResponse(BaseModel):
    traffic_limit_bytes: int
    data: list[TrafficDataPoint]

