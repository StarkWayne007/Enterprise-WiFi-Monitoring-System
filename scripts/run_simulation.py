import asyncio

from app.services.telemetry.simulator.generator import SimulationEventGenerator
from app.services.telemetry.simulator.sender import TelemetrySender


async def main():
    generator = SimulationEventGenerator()
    sender = TelemetrySender()

    devices = [
        (
    	    "AA:BB:CC:DD:EE:05",
    	    "192.168.10.5",
     	    "laptop-01",
            "Simulated Vendor",
    	    "Laptop",
        ),
        (
      	    "AA:BB:CC:DD:EE:06",
     	    "192.168.10.6",
    	    "smartphone-01",
    	    "Simulated Vendor",
    	    "Smartphone",
        ),
        (
    	    "AA:BB:CC:DD:EE:30",
     	    "192.168.10.30",
            "workstation-01",
    	    "Simulated Vendor",
            "Workstation",
        ),
    ]
    for mac, ip, hostname, vendor, device_type in devices:
        await sender.send(
            generator.device_seen(
                mac,
                ip,
                hostname,
                vendor,
                device_type,
            )
       )

    normal_traffic = [
        ("AA:BB:CC:DD:EE:05", "192.168.10.5", 1200),
        ("AA:BB:CC:DD:EE:06", "192.168.10.6", 1800),
        ("AA:BB:CC:DD:EE:30", "192.168.10.30", 1500),
    ]

    for mac, ip, byte_count in normal_traffic:
        await sender.send(
            generator.traffic(
                mac,
                ip,
                "192.168.10.10",
                "TCP",
                byte_count,
            )
        )

    await sender.send(
        generator.traffic(
            "AA:BB:CC:DD:EE:30",
            "192.168.10.30",
            "192.168.10.10",
            "TCP",
            10000,
        )
    )

    print("Simulation completed successfully")


asyncio.run(main())
