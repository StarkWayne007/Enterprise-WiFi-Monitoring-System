from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.telemetry_event import TelemetryEventRecord
from app.services.telemetry.event import TelemetryEvent
from app.services.detection import DetectionService


class TelemetryService:
    detection_service = DetectionService()

    async def process_event(
        self,
        event: TelemetryEvent,
        db: AsyncSession,
    ) -> TelemetryEvent:

        if event.event_type == "device_seen" and event.device_mac:
            result = await db.execute(
                select(Device).where(
                    Device.mac_address == event.device_mac
                )
            )

            device = result.scalar_one_or_none()

            if device is None:
                device = Device(
                    mac_address=event.device_mac,
                    ip_address=event.ip_address,
                    hostname=event.hostname,
                    vendor=event.vendor,
                    device_type=event.device_type,
                )
                db.add(device)
            else:
                if event.ip_address is not None:
                    device.ip_address = event.ip_address

                if event.hostname is not None:
                    device.hostname = event.hostname

                if event.vendor is not None:
                    device.vendor = event.vendor

                if event.device_type is not None:
                    device.device_type = event.device_type


        record = TelemetryEventRecord(
            timestamp=event.timestamp,
            event_type=event.event_type,
            source=event.source,
            device_mac=event.device_mac,
            ip_address=event.ip_address,
            destination_ip=event.destination_ip,
            protocol=event.protocol,
            bytes_transferred=event.bytes_transferred,
        )

        db.add(record)
        await db.flush()

        if event.event_type == "traffic" and event.device_mac:
            await self.detection_service.check_traffic_threshold(
                db,
                event.device_mac,
            )

            await self.detection_service.check_event_frequency(
                db,
                event.device_mac,
            )

        await db.commit()

        print(
            f"[TELEMETRY] {event.timestamp} | "
            f"{event.source} | "
            f"{event.event_type} | "
            f"{event.ip_address}"
        )

        return event
