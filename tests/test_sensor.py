"""Tests for Blauberg S21 telemetry sensors."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory
from pybls21.models import ClimateDevice, FreezeProtectionMode, HVACMode, MainHeaterType

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
        hvac_mode=HVACMode.AUTO,
        current_intake_temperature=10.5,
        current_temperature=20.0,
        extract_air_inlet_temperature=None,
        exhaust_air_outlet_temperature=8.0,
        supply_fan_speed=1010,
        extract_fan_speed=990,
        heat_exchanger_control_percent=37,
        heat_exchanger_status_percent=64,
        configured_main_heater_type=MainHeaterType.OFF,
        configured_freeze_protection_mode=FreezeProtectionMode.OFF,
        after_preheater_temperature=None,
        before_main_heater_temperature=None,
        preheater_pid_control_signal_percent=0,
        main_heater_pid_control_signal_percent=100,
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

    assert len(sensors) == 17
    assert sensors["supply_air_inlet_temperature"].native_value == 10.5
    assert sensors["supply_air_outlet_temperature"].native_value == 20.0
    assert sensors["extract_air_inlet_temperature"].native_value is None
    assert (
        sensors["supply_fan_speed"].native_unit_of_measurement == REVOLUTIONS_PER_MINUTE
    )
    assert sensors["supply_fan_speed"].device_class is None
    assert sensors["supply_fan_speed"].state_class is SensorStateClass.MEASUREMENT
    assert sensors["heat_exchanger_control_signal"].native_value == 37
    assert (
        sensors["heat_exchanger_control_signal"].native_unit_of_measurement
        == PERCENTAGE
    )
    assert (
        sensors["heat_exchanger_control_signal"].state_class
        is SensorStateClass.MEASUREMENT
    )
    assert (
        sensors["heat_exchanger_control_signal"].entity_description.entity_category
        is EntityCategory.DIAGNOSTIC
    )
    assert (
        sensors[
            "heat_exchanger_control_signal"
        ].entity_description.entity_registry_enabled_default
        is False
    )
    assert sensors["heat_recovery_activity"].native_value == 36
    assert sensors["heat_recovery_activity"].native_unit_of_measurement == PERCENTAGE
    assert sensors["heat_recovery_activity"].state_class is SensorStateClass.MEASUREMENT
    assert sensors["configured_main_heater_type"].native_value == "off"
    assert sensors["configured_freeze_protection_mode"].native_value == "off"
    assert (
        sensors["configured_main_heater_type"].entity_description.entity_category
        is EntityCategory.DIAGNOSTIC
    )
    assert sensors["after_preheater_temperature"].native_value is None
    assert (
        sensors[
            "after_preheater_temperature"
        ].entity_description.entity_registry_enabled_default
        is False
    )
    assert sensors["preheater_pid_control_signal"].native_value == 0
    assert sensors["main_heater_pid_control_signal"].native_value == 100
    assert (
        sensors[
            "preheater_pid_control_signal"
        ].entity_description.entity_registry_enabled_default
        is False
    )
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


def test_pybls21_exposes_heat_exchanger_status() -> None:
    """The pinned library contract includes controller-confirmed actuator status."""
    assert "heat_exchanger_status_percent" in ClimateDevice._fields


@pytest.mark.parametrize(
    ("raw_status", "expected_activity"),
    [(0, 100), (50, 50), (100, 0), (None, None), (-1, None), (101, None)],
)
def test_heat_recovery_activity_boundaries(
    coordinator, config_entry, raw_status, expected_activity
) -> None:
    """Inverse controller status is exposed as intuitive recovery activity."""
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "heat_recovery_activity"
    )
    sensor = BlaubergS21Sensor(coordinator, config_entry, description)
    coordinator.data.heat_exchanger_status_percent = raw_status

    assert sensor.native_value == expected_activity


@pytest.mark.parametrize("raw_status", [0, None, -1, 101])
def test_heat_recovery_activity_is_zero_when_unit_is_off(
    coordinator, config_entry, raw_status
) -> None:
    """A stopped ventilation unit cannot have active heat recovery."""
    description = next(
        item for item in SENSOR_DESCRIPTIONS if item.key == "heat_recovery_activity"
    )
    sensor = BlaubergS21Sensor(coordinator, config_entry, description)
    coordinator.data.hvac_mode = HVACMode.OFF
    coordinator.data.heat_exchanger_status_percent = raw_status

    assert sensor.native_value == 0


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
