import asyncio

from app.database.dependencies import get_db
from app.services.capture.settings import CaptureSettingsService
from app.services.capture.tshark_capture import TsharkCapture
from app.services.telemetry.service import TelemetryService
from subprocess import CalledProcessError


class CaptureRunner:

    def __init__(self):
        self.telemetry_service = TelemetryService()
        self.settings_service = CaptureSettingsService()
        self.capture = None

    async def run_once(
        self,
        interface: str,
        packet_count: int,
    ):
        self.capture = TsharkCapture(interface)
        events = self.capture.capture(packet_count)

        async for db in get_db():
            for event in events:
                await self.telemetry_service.process_event(event, db)

        return len(events)

    async def run_continuous(self):
        print("[CAPTURE] Continuous capture started.")
        print("[CAPTURE] Press Ctrl+C to stop.")

        try:
            while True:
                async for db in get_db():
                    settings = await self.settings_service.get_settings(db)

                try:
                    count = await self.run_once(
                        settings.interface,
                        settings.packet_count,
                    )
                except CalledProcessError as exc:
                    print(
                        f"[CAPTURE] TShark failed on {settings.interface}: "
                        f"{exc}"
                    )
                    await asyncio.sleep(settings.interval_seconds)
                    continue
                except FileNotFoundError:
                    print("[CAPTURE] TShark is not installed or not available in PATH.")
                    return

                except ValueError as exc:
                    print(f"[CAPTURE] Configuration error: {exc}")
                    await asyncio.sleep(settings.interval_seconds)
                    continue

                except PermissionError:
                    print(
                        f"[CAPTURE] Processed {count} packets "
                        f"on {settings.interface}."
                    )

                await asyncio.sleep(settings.interval_seconds)
                continue

        except asyncio.CancelledError:
            print("[CAPTURE] Capture stopped.")
            return


async def main():
    runner = CaptureRunner()

    try:
        await runner.run_continuous()
    except KeyboardInterrupt:
        print("[CAPTURE] Capture stopped by user.")


if __name__ == "__main__":
    asyncio.run(main())

