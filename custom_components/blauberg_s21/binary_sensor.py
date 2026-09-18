"""Binary sensors exposing Blauberg S21 operating state."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pybls21.models import HeatExchangerType, HVACMode

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0

ROTARY_HEAT_EXCHANGER_TYPES = {
    HeatExchangerType.ROTARY_DISCRETE,
    HeatExchangerType.ROTARY_ANALOG,
}


def _valid_status(value: Any) -> int | float | None:
    """Return a valid inverse status percentage or None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if 0 <= value <= 100 else None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the rotor state sensor for rotary heat exchangers."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    if coordinator.data.heat_exchanger_type not in ROTARY_HEAT_EXCHANGER_TYPES:
        return

    async_add_entities([BlaubergS21RotorRunningBinarySensor(coordinator, config_entry)])


class BlaubergS21RotorRunningBinarySensor(BlaubergS21Entity, BinarySensorEntity):
    """Report the controller-confirmed rotary heat-exchanger state."""

    _attr_has_entity_name = True
    _attr_translation_key = "rotor_running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize rotor state."""
        super().__init__(coordinator, config_entry)
        base_unique_id = self.base_unique_id
        if base_unique_id:
            self._attr_unique_id = f"{base_unique_id}_rotor_running"

    @property
    def is_on(self) -> bool | None:
        """Return whether the controller reports active heat recovery."""
        if self._device is None:
            return None
        if getattr(self._device, "hvac_mode", None) == HVACMode.OFF:
            return False
        status = _valid_status(
            getattr(self._device, "heat_exchanger_status_percent", None)
        )
        if status is None:
            return None
        return status < 100
