from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.models.telemetry_event import TelemetryEventRecord
from app.database.dependencies import get_db
from app.services.telemetry.event import TelemetryEvent
from app.services.telemetry.service import TelemetryService
from app.schemas.telemetry import TelemetryEventResponse
from app.models.system_setting import SystemSetting
from app.schemas.telemetry import TrafficHistoryResponse

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

telemetry_service = TelemetryService()


@router.post("/events")
async def receive_event(
    event: TelemetryEvent,
    db: AsyncSession = Depends(get_db),
) -> TelemetryEvent:
    return await telemetry_service.process_event(event, db)

@router.get("/events", response_model=list[TelemetryEventResponse])
async def get_telemetry_events(
    db: AsyncSession = Depends(get_db),
) -> list[TelemetryEventRecord]:
    result = await db.execute(
        select(TelemetryEventRecord).order_by(
            TelemetryEventRecord.timestamp.desc()
        )
    )
    return list(result.scalars().all())

@router.get("/traffic-history", response_model=TrafficHistoryResponse)
async def get_traffic_history(
    minutes: int = Query(default=60, gt=0, le=1440),
    db: AsyncSession = Depends(get_db),
):
    window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    events_result = await db.execute(
        select(
            TelemetryEventRecord.timestamp,
            TelemetryEventRecord.bytes_transferred,
        )
        .where(
            TelemetryEventRecord.event_type == "traffic",
            TelemetryEventRecord.timestamp >= window_start,
        )
        .order_by(TelemetryEventRecord.timestamp.asc())
    )

    settings_result = await db.execute(
        select(SystemSetting).where(SystemSetting.id == 1)
    )

    settings = settings_result.scalar_one_or_none()

    traffic_limit = (
        settings.traffic_limit_bytes
        if settings
        else 1_000_000
    )

    return {
        "traffic_limit_bytes": traffic_limit,
        "data": [
            {
                "timestamp": row.timestamp,
                "bytes_transferred": row.bytes_transferred,
            }
            for row in events_result
        ],
    }


