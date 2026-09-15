import subprocess
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.capture_setting import CaptureSetting


class CaptureSettingsService:

    def interface_exists(self, interface: str) -> bool:
        result = subprocess.run(
            ["ip", "link", "show", interface],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    async def get_settings(self, db: AsyncSession) -> CaptureSetting:
        result = await db.execute(
            select(CaptureSetting).where(CaptureSetting.id == 1)
        )

        settings = result.scalar_one_or_none()

        if settings is None:
            settings = CaptureSetting(
                id=1,
                interface="eth0",
                packet_count=10,
                interval_seconds=2,
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        return settings

    async def update_settings(
        self,
        db: AsyncSession,
        interface: str,
        packet_count: int,
        interval_seconds: int,
    ) -> CaptureSetting:

        if not self.interface_exists(interface):
            raise ValueError(f"Network interface '{interface}' does not exist")

        settings = await self.get_settings(db)

        settings.interface = interface
        settings.packet_count = packet_count
        settings.interval_seconds = interval_seconds

        await db.commit()
        await db.refresh(settings)

        return settings
