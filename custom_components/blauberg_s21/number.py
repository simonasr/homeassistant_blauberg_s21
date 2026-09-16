"""Number controls for the Blauberg S21 integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blauberg S21 number controls."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities([BlaubergS21ManualFanSpeedNumber(coordinator, config_entry)])


class BlaubergS21ManualFanSpeedNumber(BlaubergS21Entity, NumberEntity):
    """Configure the fan speed used by the custom fan mode."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_mode = NumberMode.AUTO
    _attr_native_max_value = 100
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "manual_fan_speed"

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the manual fan speed number."""
        super().__init__(coordinator, config_entry)
        if base_unique_id := self.base_unique_id:
            self._attr_unique_id = f"{base_unique_id}_manual_fan_speed"

    @property
    def native_value(self) -> int | None:
        """Return the confirmed manual fan speed percentage."""
        if self._device is None:
            return None
        return self._device.manual_fan_speed_percent

    async def async_set_native_value(self, value: float) -> None:
        """Set the custom-mode fan speed and refresh coordinated state."""
        speed_percent = int(value)
        if speed_percent != value:
            raise ValueError("Manual fan speed must be a whole percentage")
        await self.coordinator.client.set_manual_fan_speed_percent(speed_percent)
        await self.coordinator.async_request_refresh()
