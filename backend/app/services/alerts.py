from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_alert import SecurityAlert


class AlertService:
    async def create_traffic_alert(
        self,
        db: AsyncSession,
        device_mac: str,
        total_bytes: int,
    ) -> SecurityAlert:
        alert = SecurityAlert(
            device_mac=device_mac,
            alert_type="high_traffic",
            severity="medium",
            description=(
                f"Device generated {total_bytes} bytes of traffic, "
                "exceeding the configured behavioral threshold."
            ),
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        return alert
