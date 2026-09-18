"""Sensors exposing Blauberg S21 telemetry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BlaubergS21SensorEntityDescription(SensorEntityDescription):
    """Describe a Blauberg S21 telemetry sensor."""

    attribute: str
    value_fn: Callable[[Any], Any] | None = None


def _enum_name(value: Any) -> str | None:
    """Return a stable lowercase state for a protocol enum."""
    return None if value is None else value.name.lower()


def _heat_recovery_activity(value: Any) -> int | float | None:
    """Convert inverse controller status to intuitive recovery activity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not 0 <= value <= 100:
        return None
    return 100 - value


SENSOR_DESCRIPTIONS: tuple[BlaubergS21SensorEntityDescription, ...] = (
    BlaubergS21SensorEntityDescription(
        key="supply_air_inlet_temperature",
        translation_key="supply_air_inlet_temperature",
        attribute="current_intake_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="supply_air_outlet_temperature",
        translation_key="supply_air_outlet_temperature",
        attribute="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="extract_air_inlet_temperature",
        translation_key="extract_air_inlet_temperature",
        attribute="extract_air_inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="exhaust_air_outlet_temperature",
        translation_key="exhaust_air_outlet_temperature",
        attribute="exhaust_air_outlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="supply_fan_speed",
        translation_key="supply_fan_speed",
        attribute="supply_fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="extract_fan_speed",
        translation_key="extract_fan_speed",
        attribute="extract_fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="heat_exchanger_control_signal",
        translation_key="heat_exchanger_control_signal",
        attribute="heat_exchanger_control_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlaubergS21SensorEntityDescription(
        key="heat_recovery_activity",
        translation_key="heat_recovery_activity",
        attribute="heat_exchanger_status_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_heat_recovery_activity,
    ),
    BlaubergS21SensorEntityDescription(
        key="configured_main_heater_type",
        translation_key="configured_main_heater_type",
        attribute="configured_main_heater_type",
        device_class=SensorDeviceClass.ENUM,
        options=["off", "electric", "water"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_enum_name,
    ),
    BlaubergS21SensorEntityDescription(
        key="configured_freeze_protection_mode",
        translation_key="configured_freeze_protection_mode",
        attribute="configured_freeze_protection_mode",
        device_class=SensorDeviceClass.ENUM,
        options=["off", "preheating", "bypass_or_rotor", "fan_imbalance"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_enum_name,
    ),
    BlaubergS21SensorEntityDescription(
        key="after_preheater_temperature",
        translation_key="after_preheater_temperature",
        attribute="after_preheater_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlaubergS21SensorEntityDescription(
        key="before_main_heater_temperature",
        translation_key="before_main_heater_temperature",
        attribute="before_main_heater_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlaubergS21SensorEntityDescription(
        key="preheater_pid_control_signal",
        translation_key="preheater_pid_control_signal",
        attribute="preheater_pid_control_signal_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlaubergS21SensorEntityDescription(
        key="main_heater_pid_control_signal",
        translation_key="main_heater_pid_control_signal",
        attribute="main_heater_pid_control_signal_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BlaubergS21SensorEntityDescription(
        key="filter_remaining_time",
        translation_key="filter_remaining_time",
        attribute="filter_remaining_minutes",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BlaubergS21SensorEntityDescription(
        key="total_working_time",
        translation_key="total_working_time",
        attribute="total_working_time_minutes",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    BlaubergS21SensorEntityDescription(
        key="alarm_status",
        translation_key="alarm_status",
        attribute="alarm_state",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blauberg S21 telemetry sensors."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        [
            BlaubergS21Sensor(coordinator, config_entry, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )


class BlaubergS21Sensor(BlaubergS21Entity, SensorEntity):
    """Representation of one Blauberg S21 telemetry value."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: BlaubergS21SensorEntityDescription,
    ) -> None:
        """Initialize a telemetry sensor."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        base_unique_id = self.base_unique_id
        if base_unique_id:
            self._attr_unique_id = f"{base_unique_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the latest raw value without converting missing values."""
        if self._device is None:
            return None
        value = getattr(self._device, self.entity_description.attribute, None)
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(value)
        return value
