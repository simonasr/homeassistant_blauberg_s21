"""Shared entity support for the Blauberg S21 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator


class BlaubergS21Entity(CoordinatorEntity[BlaubergS21DataUpdateCoordinator]):
    """Base entity backed by the shared Blauberg S21 coordinator."""

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the shared entity state."""
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def _device(self) -> Any:
        """Return the most recently coordinated device state."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Report availability from both the coordinator and device state."""
        return bool(
            self.coordinator.last_update_success
            and self._device is not None
            and self._device.available
        )

    @property
    def base_unique_id(self) -> str | None:
        """Return the identifier used by the original climate entity."""
        if self._config_entry.unique_id:
            return self._config_entry.unique_id
        if self._device:
            return self._device.unique_id
        return None

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return information used by Home Assistant to register the device."""
        unique_id = self.base_unique_id
        if not unique_id:
            return None

        device = self._device
        name = self._config_entry.title
        manufacturer = None
        model = None
        sw_version = None

        if device:
            name = device.name or name
            manufacturer = device.manufacturer
            model = device.model
            sw_version = device.sw_version

        return DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=name,
            manufacturer=manufacturer,
            model=model,
            sw_version=sw_version,
        )
