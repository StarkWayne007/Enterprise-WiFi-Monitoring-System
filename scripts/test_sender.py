import asyncio

from app.services.telemetry.simulator.generator import SimulationEventGenerator
from app.services.telemetry.simulator.sender import TelemetrySender


async def main():
    event = SimulationEventGenerator().traffic(
        "AA:BB:CC:DD:EE:30",
        "192.168.10.30",
        "192.168.10.10",
        "TCP",
        4096,
    )

    await TelemetrySender().send(event)

    print("Telemetry event sent successfully")


asyncio.run(main())
