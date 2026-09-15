import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_receive_telemetry_event(client):
    response = await client.post(
        "/telemetry/events",
        json={
            "event_type": "traffic",
            "source": "packet_tracer",
            "device_mac": "AA:BB:CC:DD:EE:20",
            "ip_address": "192.168.10.20",
            "destination_ip": "192.168.10.10",
            "protocol": "TCP",
            "bytes_transferred": 2048,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_type"] == "traffic"
    assert data["source"] == "packet_tracer"
    assert data["device_mac"] == "AA:BB:CC:DD:EE:20"
    assert data["bytes_transferred"] == 2048
