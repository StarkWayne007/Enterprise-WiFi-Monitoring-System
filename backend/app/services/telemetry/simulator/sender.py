import httpx

from app.services.telemetry.event import TelemetryEvent


class TelemetrySender:
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url

    async def send(self, event: TelemetryEvent) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/telemetry/events",
                json=event.model_dump(mode="json"),
            )

        response.raise_for_status()
