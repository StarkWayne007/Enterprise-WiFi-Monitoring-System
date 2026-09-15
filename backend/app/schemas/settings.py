from pydantic import BaseModel, Field, EmailStr


class TrafficLimitResponse(BaseModel):
    traffic_limit_bytes: int


class TrafficLimitUpdate(BaseModel):
    traffic_limit_bytes: int = Field(gt=0)


class EventFrequencyResponse(BaseModel):
    event_frequency_limit: int


class EventFrequencyUpdate(BaseModel):
    event_frequency_limit: int = Field(gt=0)


class BehaviorWindowResponse(BaseModel):
    behavior_window_minutes: int


class BehaviorWindowUpdate(BaseModel):
    behavior_window_minutes: int = Field(gt=0, le=1440)


class TechnicianEmailResponse(BaseModel):
    technician_email: EmailStr


class TechnicianEmailUpdate(BaseModel):
    technician_email: EmailStr


class CaptureSettingsResponse(BaseModel):
    interface: str
    packet_count: int
    interval_seconds: int


class CaptureSettingsUpdate(BaseModel):
    interface: str
    packet_count: int = Field(gt=0, le=1000)
    interval_seconds: int = Field(gt=0, le=3600)
