from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry_event import TelemetryEventRecord


class UsageService:
    async def get_device_usage(
        self,
        db: AsyncSession,
    ) -> list[dict]:
        result = await db.execute(
            select(
                TelemetryEventRecord.device_mac,
                func.sum(
                    TelemetryEventRecord.bytes_transferred
                ).label("total_bytes"),
            )
            .where(
                TelemetryEventRecord.device_mac.is_not(None),
            )
            .group_by(
                TelemetryEventRecord.device_mac,
            )
        )

        return [
            {
                "device_mac": row.device_mac,
                "total_bytes": row.total_bytes or 0,
            }
            for row in result
        ]
