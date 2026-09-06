"""Tests for coordinator-backed Blauberg S21 climate controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.components.climate.const import FAN_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.blauberg_s21.climate import BlS21ClimateEntity
from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator


@pytest.fixture
def config_entry():
    """Return the minimal config-entry attributes used by the climate entity."""
    return SimpleNamespace(unique_id="synthetic-device", title="Test unit")


@pytest.fixture
def device():
    """Return the synthetic device attributes read by the climate entity."""
    return SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
        fan_mode=1,
        max_fan_level=3,
    )


@pytest.fixture
def coordinator(hass, device):
    """Return a coordinator whose refresh can be inspected."""
    client = SimpleNamespace(
        set_hvac_mode=AsyncMock(),
        set_fan_mode=AsyncMock(),
        set_temperature=AsyncMock(),
        reset_filter_change_timer=AsyncMock(),
        reset_alarm=AsyncMock(),
    )
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)
    coordinator.data = device
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


async def test_climate_identity_matches_existing_climate_entity(
    coordinator, config_entry
) -> None:
    """The coordinator conversion preserves the climate identity and device."""
    entity = BlS21ClimateEntity(coordinator, config_entry)

    assert entity.unique_id == "synthetic-device"
    assert entity.name == "Test unit"
    assert entity.device_info["identifiers"] == {("blauberg_s21", "synthetic-device")}


@pytest.mark.parametrize(
    ("method", "args", "kwargs", "client_method"),
    [
        ("async_set_hvac_mode", (HVACMode.AUTO,), {}, "set_hvac_mode"),
        ("async_set_temperature", (), {ATTR_TEMPERATURE: 21}, "set_temperature"),
        ("async_reset_filter_change_timer", (), {}, "reset_filter_change_timer"),
        ("async_reset_alarm", (), {}, "reset_alarm"),
    ],
)
async def test_commands_request_one_coordinator_refresh(
    coordinator, config_entry, method, args, kwargs, client_method
) -> None:
    """Every write command requests exactly one coordinated refresh."""
    entity = BlS21ClimateEntity(coordinator, config_entry)

    await getattr(entity, method)(*args, **kwargs)

    getattr(coordinator.client, client_method).assert_awaited_once()
    coordinator.async_request_refresh.assert_awaited_once()


async def test_fan_logbook_requires_a_confirmed_changed_refresh(
    hass, coordinator, config_entry
) -> None:
    """Fan changes only log after the post-command refresh confirms them."""
    entity = BlS21ClimateEntity(coordinator, config_entry)
    entity.hass = hass
    entity.entity_id = "climate.test_unit"
    logbook_entries = []
    hass.bus.async_listen(
        "logbook_entry", lambda event: logbook_entries.append(event.data)
    )

    async def refresh() -> None:
        coordinator.data.fan_mode = 2

    coordinator.async_request_refresh.side_effect = refresh
    await entity.async_set_fan_mode(FAN_MEDIUM)

    coordinator.client.set_fan_mode.assert_awaited_once_with(2)
    coordinator.async_request_refresh.assert_awaited_once()
    await hass.async_block_till_done()
    assert logbook_entries == [
        {
            "name": "Test unit",
            "message": "Fan mode changed: low -> medium",
            "entity_id": "climate.test_unit",
            "domain": "blauberg_s21",
        }
    ]


async def test_failed_write_does_not_request_refresh(coordinator, config_entry) -> None:
    """A failed device command must not pretend that state was refreshed."""
    entity = BlS21ClimateEntity(coordinator, config_entry)
    coordinator.client.set_temperature.side_effect = OSError("write failed")

    with pytest.raises(OSError, match="write failed"):
        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 21})

    coordinator.async_request_refresh.assert_not_awaited()
