from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_mac: str | None
    alert_type: str
    severity: str
    description: str
    status: str
    created_at: datetime
