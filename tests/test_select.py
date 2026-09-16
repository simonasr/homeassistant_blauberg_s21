"""Tests for Blauberg S21 select controls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.const import EntityCategory
from pybls21.models import HeatExchangerMode, HeatExchangerType

from custom_components.blauberg_s21.const import DOMAIN
from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator
from custom_components.blauberg_s21.select import (
    OPTION_AUTO,
    OPTION_ROTOR_OFF,
    OPTION_ROTOR_ON,
    BlaubergS21RotorModeSelect,
    async_setup_entry,
)


@pytest.fixture
def config_entry():
    """Return the config-entry attributes used by the select."""
    return SimpleNamespace(
        entry_id="test-entry", unique_id="synthetic-device", title="Test unit"
    )


@pytest.fixture
def device():
    """Return synthetic discrete-rotor device data."""
    return SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
        heat_exchanger_type=HeatExchangerType.ROTARY_DISCRETE,
        heat_exchanger_mode=HeatExchangerMode.AUTO,
    )


@pytest.fixture
def coordinator(hass, device):
    """Return a successful coordinator with inspectable writes."""
    client = SimpleNamespace(set_heat_exchanger_mode=AsyncMock())
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)
    coordinator.data = device
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_rotor_select_metadata_and_state(coordinator, config_entry) -> None:
    """The rotor select has stable identity and maps confirmed state."""
    entity = BlaubergS21RotorModeSelect(coordinator, config_entry)

    assert entity.unique_id == "synthetic-device_rotor_mode"
    assert entity.entity_category is EntityCategory.CONFIG
    assert entity.options == [OPTION_AUTO, OPTION_ROTOR_ON, OPTION_ROTOR_OFF]
    assert entity.current_option == OPTION_AUTO
    assert entity.device_info["identifiers"] == {("blauberg_s21", "synthetic-device")}


async def test_rotor_select_command_refreshes_confirmed_state(
    coordinator, config_entry
) -> None:
    """A valid selection writes the protocol enum and refreshes once."""
    entity = BlaubergS21RotorModeSelect(coordinator, config_entry)

    await entity.async_select_option(OPTION_ROTOR_OFF)

    coordinator.client.set_heat_exchanger_mode.assert_awaited_once_with(
        HeatExchangerMode.BYPASS
    )
    coordinator.async_request_refresh.assert_awaited_once()


async def test_rotor_select_rejects_unknown_option(coordinator, config_entry) -> None:
    """Unknown options fail before opening a device write."""
    entity = BlaubergS21RotorModeSelect(coordinator, config_entry)

    with pytest.raises(ValueError, match="Unsupported rotor mode"):
        await entity.async_select_option("unexpected")

    coordinator.client.set_heat_exchanger_mode.assert_not_awaited()
    coordinator.async_request_refresh.assert_not_awaited()


async def test_setup_only_adds_select_for_discrete_rotor(
    hass, coordinator, config_entry
) -> None:
    """Unsupported heat exchanger hardware does not get an unsafe control."""
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator
    add_entities = Mock()

    await async_setup_entry(hass, config_entry, add_entities)

    added = add_entities.call_args.args[0]
    assert len(added) == 1
    assert isinstance(added[0], BlaubergS21RotorModeSelect)

    coordinator.data.heat_exchanger_type = HeatExchangerType.NOT_AVAILABLE
    add_entities.reset_mock()
    await async_setup_entry(hass, config_entry, add_entities)
    add_entities.assert_not_called()
