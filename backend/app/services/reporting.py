from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.security_alert import SecurityAlert
from app.models.telemetry_event import TelemetryEventRecord
from app.services.behavior import BehaviorService


class ReportingService:
    behavior_service = BehaviorService()

    async def get_report_summary(self, db: AsyncSession) -> dict:
        device_count = await db.scalar(
            select(func.count(Device.id))
        )

        traffic_event_count = await db.scalar(
            select(func.count(TelemetryEventRecord.id))
            .where(TelemetryEventRecord.event_type == "traffic")
        )

        total_bytes = await db.scalar(
            select(
                func.coalesce(
                    func.sum(TelemetryEventRecord.bytes_transferred),
                    0,
                )
            )
            .where(TelemetryEventRecord.event_type == "traffic")
        )

        alert_count = await db.scalar(
            select(func.count(SecurityAlert.id))
        )

        unresolved_alert_count = await db.scalar(
            select(func.count(SecurityAlert.id))
            .where(SecurityAlert.status != "resolved")
        )

        return {
            "device_count": device_count or 0,
            "traffic_event_count": traffic_event_count or 0,
            "total_bytes": total_bytes or 0,
            "alert_count": alert_count or 0,
            "unresolved_alert_count": unresolved_alert_count or 0,
        }

    async def get_report_detail(self, db: AsyncSession) -> dict:
        behavior_result = (
            await self.behavior_service.get_device_behavior(db)
        )

        devices_result = await db.execute(
            select(Device).order_by(Device.last_seen.desc())
        )

        alerts_result = await db.execute(
            select(SecurityAlert)
            .order_by(SecurityAlert.created_at.desc())
        )

        traffic_result = await db.execute(
            select(TelemetryEventRecord)
            .where(TelemetryEventRecord.event_type == "traffic")
            .order_by(TelemetryEventRecord.timestamp.desc())
        )

        devices = devices_result.scalars().all()
        alerts = alerts_result.scalars().all()
        traffic_events = traffic_result.scalars().all()

        return {
            "devices": [
                {
                    "id": device.id,
                    "mac_address": device.mac_address,
                    "ip_address": device.ip_address,
                    "hostname": device.hostname,
                    "vendor": device.vendor,
                    "device_type": device.device_type,
                    "first_seen": device.first_seen,
                    "last_seen": device.last_seen,
                }
                for device in devices
            ],
            "alerts": [
                {
                    "id": alert.id,
                    "device_mac": alert.device_mac,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "description": alert.description,
                    "status": alert.status,
                    "created_at": alert.created_at,
                }
                for alert in alerts
            ],
            "traffic_events": [
                {
                    "timestamp": event.timestamp,
                    "device_mac": event.device_mac,
                    "destination_ip": event.destination_ip,
                    "protocol": event.protocol,
                    "bytes_transferred": event.bytes_transferred,
                }
                for event in traffic_events
            ],
            "behavior": behavior_result,
        }

