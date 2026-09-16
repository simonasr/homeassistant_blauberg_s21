"""Tests for Blauberg S21 number controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.const import PERCENTAGE, EntityCategory

from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator
from custom_components.blauberg_s21.number import BlaubergS21ManualFanSpeedNumber


@pytest.fixture
def config_entry():
    """Return the config-entry attributes used by the number."""
    return SimpleNamespace(unique_id="synthetic-device", title="Test unit")


@pytest.fixture
def coordinator(hass):
    """Return a successful coordinator with synthetic fan state."""
    device = SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
        manual_fan_speed_percent=42,
    )
    client = SimpleNamespace(set_manual_fan_speed_percent=AsyncMock())
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)
    coordinator.data = device
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_manual_fan_number_metadata_and_value(coordinator, config_entry) -> None:
    """The fan number exposes the protocol range and confirmed value."""
    entity = BlaubergS21ManualFanSpeedNumber(coordinator, config_entry)

    assert entity.unique_id == "synthetic-device_manual_fan_speed"
    assert entity.entity_category is EntityCategory.CONFIG
    assert entity.native_min_value == 0
    assert entity.native_max_value == 100
    assert entity.native_step == 1
    assert entity.native_unit_of_measurement == PERCENTAGE
    assert entity.native_value == 42


async def test_manual_fan_number_command_refreshes_state(
    coordinator, config_entry
) -> None:
    """A whole percentage is written and followed by one refresh."""
    entity = BlaubergS21ManualFanSpeedNumber(coordinator, config_entry)

    await entity.async_set_native_value(67)

    coordinator.client.set_manual_fan_speed_percent.assert_awaited_once_with(67)
    coordinator.async_request_refresh.assert_awaited_once()


async def test_manual_fan_number_rejects_fraction(coordinator, config_entry) -> None:
    """Fractional values fail before opening a device write."""
    entity = BlaubergS21ManualFanSpeedNumber(coordinator, config_entry)

    with pytest.raises(ValueError, match="whole percentage"):
        await entity.async_set_native_value(42.5)

    coordinator.client.set_manual_fan_speed_percent.assert_not_awaited()
    coordinator.async_request_refresh.assert_not_awaited()
