from pydantic import ValidationError
import pytest

from app.schemas.device import DeviceCreate


def test_mac_address_normalization():
    device = DeviceCreate(
        mac_address="aa-bb-cc-dd-ee-03",
    )

    assert device.mac_address == "AA:BB:CC:DD:EE:03"


def test_invalid_mac_address():
    with pytest.raises(ValidationError):
        DeviceCreate(
            mac_address="AA:BB:CC:DD",
        )


def test_valid_mac_address():
    device = DeviceCreate(
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    assert device.mac_address == "AA:BB:CC:DD:EE:FF"