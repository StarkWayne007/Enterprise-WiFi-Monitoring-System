from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.models.system_setting import SystemSetting
from app.schemas.settings import (
    BehaviorWindowResponse,
    BehaviorWindowUpdate,
    CaptureSettingsResponse,
    CaptureSettingsUpdate,
    EventFrequencyResponse,
    EventFrequencyUpdate,
    TechnicianEmailResponse,
    TechnicianEmailUpdate,
    TrafficLimitResponse,
    TrafficLimitUpdate,
)
from app.services.capture.settings import CaptureSettingsService


router = APIRouter(prefix="/settings", tags=["Settings"])

service = CaptureSettingsService()


async def get_settings(db: AsyncSession) -> SystemSetting:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.id == 1)
    )

    settings = result.scalar_one_or_none()

    if settings is None:
        settings = SystemSetting(
            id=1,
            traffic_limit_bytes=1_000_000,
            behavior_window_minutes=1440,
            event_frequency_limit=100,
            technician_email="",
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


# ─────────────────────────────────────────────
# Traffic Limit
# ─────────────────────────────────────────────

@router.get(
    "/traffic-limit",
    response_model=TrafficLimitResponse,
)
async def get_traffic_limit(
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    return {
        "traffic_limit_bytes": settings.traffic_limit_bytes,
    }


@router.put(
    "/traffic-limit",
    response_model=TrafficLimitResponse,
)
async def update_traffic_limit(
    data: TrafficLimitUpdate,
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    settings.traffic_limit_bytes = data.traffic_limit_bytes

    await db.commit()
    await db.refresh(settings)

    return {
        "traffic_limit_bytes": settings.traffic_limit_bytes,
    }


# ─────────────────────────────────────────────
# Event Frequency
# ─────────────────────────────────────────────

@router.get(
    "/event-frequency",
    response_model=EventFrequencyResponse,
)
async def get_event_frequency(
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    return {
        "event_frequency_limit": settings.event_frequency_limit,
    }


@router.put(
    "/event-frequency",
    response_model=EventFrequencyResponse,
)
async def update_event_frequency(
    data: EventFrequencyUpdate,
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    settings.event_frequency_limit = data.event_frequency_limit

    await db.commit()
    await db.refresh(settings)

    return {
        "event_frequency_limit": settings.event_frequency_limit,
    }


# ─────────────────────────────────────────────
# Behavior Window
# ─────────────────────────────────────────────

@router.get(
    "/behavior-window",
    response_model=BehaviorWindowResponse,
)
async def get_behavior_window(
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    return {
        "behavior_window_minutes": settings.behavior_window_minutes,
    }


@router.put(
    "/behavior-window",
    response_model=BehaviorWindowResponse,
)
async def update_behavior_window(
    data: BehaviorWindowUpdate,
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    settings.behavior_window_minutes = data.behavior_window_minutes

    await db.commit()
    await db.refresh(settings)

    return {
        "behavior_window_minutes": settings.behavior_window_minutes,
    }


# ─────────────────────────────────────────────
# Technician Email
# ─────────────────────────────────────────────

@router.get(
    "/technician-email",
    response_model=TechnicianEmailResponse,
)
async def get_technician_email(
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    if not settings.technician_email:
        raise HTTPException(
            status_code=404,
            detail="Technician email is not configured.",
        )

    return {
        "technician_email": settings.technician_email,
    }


@router.put(
    "/technician-email",
    response_model=TechnicianEmailResponse,
)
async def update_technician_email(
    data: TechnicianEmailUpdate,
    db: AsyncSession = Depends(get_db),
):
    settings = await get_settings(db)

    settings.technician_email = str(data.technician_email)

    await db.commit()
    await db.refresh(settings)

    return {
        "technician_email": settings.technician_email,
    }


# ─────────────────────────────────────────────
# Capture Settings
# ─────────────────────────────────────────────

@router.get(
    "/capture",
    response_model=CaptureSettingsResponse,
)
async def get_capture_settings(
    db: AsyncSession = Depends(get_db),
):
    return await service.get_settings(db)


@router.put(
    "/capture",
    response_model=CaptureSettingsResponse,
)
async def update_capture_settings(
    data: CaptureSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.update_settings(
            db,
            data.interface,
            data.packet_count,
            data.interval_seconds,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

