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
async def test_get_devices(client):
    response = await client.get("/devices/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_device(client):
    response = await client.post(
        "/devices/",
        json={
            "mac_address": "AA:BB:CC:DD:EE:10",
            "ip_address": "192.168.1.110",
            "hostname": "api-test-device",
            "vendor": "Test Vendor",
            "device_type": "Laptop",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["mac_address"] == "AA:BB:CC:DD:EE:10"
    assert data["ip_address"] == "192.168.1.110"
    assert data["hostname"] == "api-test-device"


@pytest.mark.asyncio
async def test_duplicate_mac_address(client):
    mac_address = "AA:BB:CC:DD:EE:11"

    first_response = await client.post(
        "/devices/",
        json={"mac_address": mac_address},
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/devices/",
        json={"mac_address": mac_address},
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A device with this MAC address already exists."
    )
