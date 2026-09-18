"""Tests for Blauberg S21 binary sensors."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from pybls21.models import HeatExchangerType, HVACMode

from custom_components.blauberg_s21.binary_sensor import (
    BlaubergS21RotorRunningBinarySensor,
    async_setup_entry,
)
from custom_components.blauberg_s21.const import DOMAIN
from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator


@pytest.fixture
def config_entry():
    """Return the minimal config-entry attributes used by entities."""
    return SimpleNamespace(
        entry_id="test-entry", unique_id="synthetic-device", title="Test unit"
    )


@pytest.fixture
def device():
    """Return synthetic controller-confirmed rotor data."""
    return SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
        hvac_mode=HVACMode.AUTO,
        heat_exchanger_type=HeatExchangerType.ROTARY_DISCRETE,
        heat_exchanger_status_percent=0,
    )


@pytest.fixture
def coordinator(hass, device):
    """Return a successful coordinator with synthetic current data."""
    coordinator = BlaubergS21DataUpdateCoordinator(hass, SimpleNamespace())
    coordinator.data = device
    coordinator.last_update_success = True
    return coordinator


def test_rotor_running_metadata_and_state(coordinator, config_entry) -> None:
    """Rotor state has stable identity and running semantics."""
    entity = BlaubergS21RotorRunningBinarySensor(coordinator, config_entry)

    assert entity.unique_id == "synthetic-device_rotor_running"
    assert entity.device_class is BinarySensorDeviceClass.RUNNING
    assert entity.is_on is True
    assert entity.device_info["identifiers"] == {("blauberg_s21", "synthetic-device")}


@pytest.mark.parametrize(
    ("raw_status", "expected_state"),
    [(0, True), (50, True), (100, False), (None, None), (-1, None), (101, None)],
)
def test_rotor_running_boundaries(
    coordinator, config_entry, raw_status, expected_state
) -> None:
    """Inverse status percentage maps to a conservative binary state."""
    entity = BlaubergS21RotorRunningBinarySensor(coordinator, config_entry)
    coordinator.data.heat_exchanger_status_percent = raw_status

    assert entity.is_on is expected_state


@pytest.mark.parametrize("raw_status", [0, None, -1, 101])
def test_rotor_not_running_when_unit_is_off(
    coordinator, config_entry, raw_status
) -> None:
    """A stopped ventilation unit cannot have a running rotor."""
    entity = BlaubergS21RotorRunningBinarySensor(coordinator, config_entry)
    coordinator.data.hvac_mode = HVACMode.OFF
    coordinator.data.heat_exchanger_status_percent = raw_status

    assert entity.is_on is False


async def test_setup_only_adds_sensor_for_rotary_heat_exchangers(
    hass, coordinator, config_entry
) -> None:
    """Bypass heat exchangers do not get a rotor entity."""
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator
    add_entities = Mock()

    await async_setup_entry(hass, config_entry, add_entities)

    added = add_entities.call_args.args[0]
    assert len(added) == 1
    assert isinstance(added[0], BlaubergS21RotorRunningBinarySensor)

    coordinator.data.heat_exchanger_type = HeatExchangerType.ROTARY_ANALOG
    add_entities.reset_mock()
    await async_setup_entry(hass, config_entry, add_entities)
    assert len(add_entities.call_args.args[0]) == 1

    coordinator.data.heat_exchanger_type = HeatExchangerType.BYPASS_ANALOG
    add_entities.reset_mock()
    await async_setup_entry(hass, config_entry, add_entities)
    add_entities.assert_not_called()
