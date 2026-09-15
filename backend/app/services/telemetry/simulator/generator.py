from app.services.telemetry.event import TelemetryEvent


class SimulationEventGenerator:
    def device_seen(
        self,
        mac_address: str,
        ip_address: str,
        hostname: str | None = None,
        vendor: str | None = None,
        device_type: str | None = None,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_type="device_seen",
            source="packet_tracer",
            device_mac=mac_address,
            ip_address=ip_address,
            hostname=hostname,
            vendor=vendor,
            device_type=device_type,
         )

    def traffic(
        self,
        mac_address: str,
        source_ip: str,
        destination_ip: str,
        protocol: str,
        bytes_transferred: int,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_type="traffic",
            source="packet_tracer",
            device_mac=mac_address,
            ip_address=source_ip,
            destination_ip=destination_ip,
            protocol=protocol,
            bytes_transferred=bytes_transferred,
        )
