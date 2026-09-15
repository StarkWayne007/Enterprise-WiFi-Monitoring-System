import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_alert import SecurityAlert
from app.models.system_setting import SystemSetting
from app.models.telemetry_event import TelemetryEventRecord
from app.services.notifications import NotificationService


class DetectionService:
    notification_service = NotificationService()

    async def check_traffic_threshold(
        self,
        db: AsyncSession,
        device_mac: str,
    ) -> SecurityAlert | None:
        if not re.fullmatch(
            r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}",
            device_mac,
        ):
            raise ValueError("Invalid MAC address format.")

        settings_result = await db.execute(
            select(SystemSetting).where(SystemSetting.id == 1)
        )
        settings = settings_result.scalar_one_or_none()

        if settings is None:
            return None

        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.behavior_window_minutes
        )

        traffic_result = await db.execute(
            select(
                func.sum(
                    TelemetryEventRecord.bytes_transferred
                )
            ).where(
                TelemetryEventRecord.device_mac == device_mac,
                TelemetryEventRecord.event_type == "traffic",
                TelemetryEventRecord.timestamp >= window_start,
            )
        )

        total_bytes = traffic_result.scalar() or 0

        if total_bytes <= settings.traffic_limit_bytes:
            return None

        existing_result = await db.execute(
            select(SecurityAlert).where(
                SecurityAlert.device_mac == device_mac,
                SecurityAlert.alert_type == "high_traffic",
                SecurityAlert.status != "resolved",
            )
        )

        if existing_result.scalar_one_or_none() is not None:
            return None

        alert = SecurityAlert(
            device_mac=device_mac,
            alert_type="high_traffic",
            severity="medium",
            description=(
                f"Device generated {total_bytes} bytes of traffic "
                f"within the last {settings.behavior_window_minutes} minutes, "
                f"exceeding the configured limit of "
                f"{settings.traffic_limit_bytes} bytes."
            ),
        )

        db.add(alert)
        await db.flush()

        await self.notification_service.notify_alert(
        alert,
        settings.technician_email,
        )

        return alert


    async def check_event_frequency(
        self,
        db: AsyncSession,
        device_mac: str,
    ) -> SecurityAlert | None:

        if not re.fullmatch(
            r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}",
            device_mac,
        ):
            raise ValueError("Invalid MAC address format.")

        settings_result = await db.execute(
            select(SystemSetting).where(SystemSetting.id == 1)
        )
        settings = settings_result.scalar_one_or_none()

        if settings is None:
            return None

        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.behavior_window_minutes
        )

        event_result = await db.execute(
            select(
                func.count(TelemetryEventRecord.id)
            ).where(
                TelemetryEventRecord.device_mac == device_mac,
                TelemetryEventRecord.event_type == "traffic",
                TelemetryEventRecord.timestamp >= window_start,
            )
        )

        event_count = event_result.scalar() or 0

        if event_count <= settings.event_frequency_limit:
            return None

        existing_result = await db.execute(
            select(SecurityAlert).where(
                SecurityAlert.device_mac == device_mac,
                SecurityAlert.alert_type == "high_event_frequency",
                SecurityAlert.status != "resolved",
            )
        )

        if existing_result.scalar_one_or_none() is not None:
            return None

        alert = SecurityAlert(
            device_mac=device_mac,
            alert_type="high_event_frequency",
            severity="medium",
            description=(
                f"Device generated {event_count} traffic events "
                f"within the last {settings.behavior_window_minutes} minutes, "
                f"exceeding the configured limit of "
                f"{settings.event_frequency_limit} events."
            ),
        )

        db.add(alert)
        await db.flush()

        await self.notification_service.notify_alert(
        alert,
        settings.technician_email,
        )

        return alert
