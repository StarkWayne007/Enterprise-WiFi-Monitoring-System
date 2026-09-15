import subprocess
from datetime import datetime, timezone

from app.services.telemetry.event import TelemetryEvent


class TsharkCapture:

    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self.local_mac = self._get_local_mac()

    def _get_local_mac(self) -> str | None:
        result = subprocess.run(
            ["ip", "link", "show", self.interface],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("link/"):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].lower()

        return None

    def capture(self, packet_count: int = 10) -> list[TelemetryEvent]:
        command = [
            "tshark",
            "-i", self.interface,
            "-T", "fields",
            "-E", "separator=\t",
            "-e", "frame.time_epoch",
            "-e", "eth.src",
            "-e", "eth.dst",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "ip.proto",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "udp.srcport",
            "-e", "udp.dstport",
            "-e", "frame.len",
            "-c", str(packet_count),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        events = []

        for line in result.stdout.splitlines():
            fields = line.split("\t")

            if len(fields) != 11:
                print("[CAPTURE] Skipping malformed TShark output.")
                continue

            (
                timestamp,
                source_mac,
                destination_mac,
                source_ip,
                destination_ip,
                ip_protocol,
                tcp_source_port,
                tcp_destination_port,
                udp_source_port,
                udp_destination_port,
                frame_length,
            ) = fields

            if not source_ip:
                continue

            protocol = self._get_protocol(
                ip_protocol,
                tcp_source_port,
                tcp_destination_port,
                udp_source_port,
                udp_destination_port,
            )

            device_mac = None

            if source_mac.lower() == self.local_mac:
                device_mac = source_mac

            events.append(
                TelemetryEvent(
                    timestamp=datetime.fromtimestamp(
                        float(timestamp),
                        tz=timezone.utc,
                    ),
                    event_type="traffic",
                    source="tshark",
                    device_mac=device_mac,
                    ip_address=source_ip,
                    destination_ip=destination_ip or None,
                    protocol=protocol,
                    bytes_transferred=int(frame_length),
                )
            )

        return events

    @staticmethod
    def _get_protocol(
        ip_protocol: str,
        tcp_source_port: str,
        tcp_destination_port: str,
        udp_source_port: str,
        udp_destination_port: str,
    ) -> str:
        if tcp_source_port or tcp_destination_port:
            return "TCP"

        if udp_source_port or udp_destination_port:
            return "UDP"

        if ip_protocol == "1":
            return "ICMP"

        return ip_protocol or "UNKNOWN"
