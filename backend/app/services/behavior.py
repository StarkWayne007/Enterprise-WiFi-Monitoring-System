from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry_event import TelemetryEventRecord
from app.models.system_setting import SystemSetting


class BehaviorService:

    async def get_traffic_threshold(
        self,
        db: AsyncSession,
    ) -> int:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.id == 1)
        )

        settings = result.scalar_one_or_none()

        if settings is None:
            settings = SystemSetting(
                id=1,
                traffic_limit_bytes=1_000_000,
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        return settings.traffic_limit_bytes

    async def get_device_behavior(
        self,
        db: AsyncSession,
    ) -> list[dict]:

        result = await db.execute(
            select(SystemSetting).where(SystemSetting.id == 1)
        )

        settings = result.scalar_one_or_none()

        if settings is None:
            settings = SystemSetting(
                id=1,
                traffic_limit_bytes=1_000_000,
                behavior_window_minutes=5,
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        traffic_threshold = settings.traffic_limit_bytes
        behavior_window_minutes = settings.behavior_window_minutes

        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=behavior_window_minutes
        )

        result = await db.execute(
            select(
                TelemetryEventRecord.device_mac,
                func.count(TelemetryEventRecord.id).label("event_count"),
                func.coalesce(
                    func.sum(TelemetryEventRecord.bytes_transferred),
                    0,
                ).label("total_bytes"),
                func.count(
                    func.distinct(TelemetryEventRecord.destination_ip)
                ).label("unique_destinations"),
                func.min(TelemetryEventRecord.timestamp).label("first_event"),
                func.max(TelemetryEventRecord.timestamp).label("last_event"),
            )
            .where(
                TelemetryEventRecord.device_mac.is_not(None),
                TelemetryEventRecord.event_type == "traffic",
                TelemetryEventRecord.timestamp >= window_start,
            )
            .group_by(
                TelemetryEventRecord.device_mac,
            )
        )

        behaviors = []

        for row in result:
            total_bytes = row.total_bytes or 0

            window_duration_seconds = behavior_window_minutes * 60

            if window_duration_seconds > 0:
                bytes_per_second = (
                    total_bytes / window_duration_seconds
                )
            else:
                bytes_per_second = 0.0

            status = (
                "suspicious"
                if total_bytes > traffic_threshold
                else "normal"
            )

            behaviors.append(
                {
                    "device_mac": row.device_mac,
                    "event_count": row.event_count,
                    "total_bytes": total_bytes,
                    "unique_destinations": row.unique_destinations,
                    "bytes_per_second": round(bytes_per_second, 2),
                    "status": status,
                }
            )

        return behaviors

