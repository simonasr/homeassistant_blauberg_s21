"""Tests for Blauberg S21 telemetry sensors."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import REVOLUTIONS_PER_MINUTE, UnitOfTemperature, UnitOfTime

from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator
from custom_components.blauberg_s21.sensor import SENSOR_DESCRIPTIONS, BlaubergS21Sensor


@pytest.fixture
def config_entry():
    """Return the minimal config-entry attributes used by entities."""
    return SimpleNamespace(unique_id="synthetic-device", title="Test unit")


@pytest.fixture
def device():
    """Return synthetic device data with no private device details."""
    return SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
        current_intake_temperature=10.5,
        current_temperature=20.0,
        extract_air_inlet_temperature=None,
        exhaust_air_outlet_temperature=8.0,
        supply_fan_speed=1010,
        extract_fan_speed=990,
        filter_remaining_minutes=120,
        total_working_time_minutes=240,
        alarm_state=0,
    )


@pytest.fixture
def coordinator(hass, device):
    """Return a successful coordinator with synthetic current data."""
    coordinator = BlaubergS21DataUpdateCoordinator(hass, SimpleNamespace())
    coordinator.data = device
    coordinator.last_update_success = True
    return coordinator


def test_sensor_metadata_and_values(coordinator, config_entry) -> None:
    """Each sensor has its fixed mapping, metadata, and stable identity."""
    sensors = {
        description.key: BlaubergS21Sensor(coordinator, config_entry, description)
        for description in SENSOR_DESCRIPTIONS
    }

    assert len(sensors) == 9
    assert sensors["supply_air_inlet_temperature"].native_value == 10.5
    assert sensors["supply_air_outlet_temperature"].native_value == 20.0
    assert sensors["extract_air_inlet_temperature"].native_value is None
    assert (
        sensors["supply_fan_speed"].native_unit_of_measurement == REVOLUTIONS_PER_MINUTE
    )
    assert sensors["supply_fan_speed"].device_class is None
    assert sensors["supply_fan_speed"].state_class is SensorStateClass.MEASUREMENT
    assert sensors["filter_remaining_time"].device_class is SensorDeviceClass.DURATION
    assert (
        sensors["filter_remaining_time"].native_unit_of_measurement
        == UnitOfTime.MINUTES
    )
    assert (
        sensors["total_working_time"].state_class is SensorStateClass.TOTAL_INCREASING
    )
    assert sensors["alarm_status"].native_value == 0
    assert sensors["alarm_status"].device_class is None
    assert (
        sensors["supply_air_inlet_temperature"].device_class
        is SensorDeviceClass.TEMPERATURE
    )
    assert (
        sensors["supply_air_inlet_temperature"].native_unit_of_measurement
        == UnitOfTemperature.CELSIUS
    )
    assert (
        sensors["supply_air_inlet_temperature"].unique_id
        == "synthetic-device_supply_air_inlet_temperature"
    )
    assert sensors["supply_air_inlet_temperature"].device_info["identifiers"] == {
        ("blauberg_s21", "synthetic-device")
    }


def test_sensor_availability_keeps_missing_optional_values_available(
    coordinator, config_entry
) -> None:
    """A missing telemetry value is unknown, not unavailable."""
    description = next(
        item
        for item in SENSOR_DESCRIPTIONS
        if item.key == "extract_air_inlet_temperature"
    )
    sensor = BlaubergS21Sensor(coordinator, config_entry, description)

    assert sensor.available is True
    assert sensor.native_value is None

    coordinator.last_update_success = False
    assert sensor.available is False

    coordinator.last_update_success = True
    coordinator.data.available = False
    assert sensor.available is False
