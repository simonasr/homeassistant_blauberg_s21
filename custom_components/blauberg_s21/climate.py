"""Support for the Blauberg S21 climate entity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import FAN_HIGH, FAN_LOW, FAN_MEDIUM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pybls21.models import HVACAction as BlS21HVACAction
from pybls21.models import HVACMode as BlS21HVACMode

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0

HA_TO_S21_HVACMODE = {
    HVACMode.OFF: BlS21HVACMode.OFF,
    HVACMode.HEAT: BlS21HVACMode.HEAT,
    HVACMode.COOL: BlS21HVACMode.COOL,
    HVACMode.AUTO: BlS21HVACMode.AUTO,
    HVACMode.FAN_ONLY: BlS21HVACMode.FAN_ONLY,
}

S21_TO_HA_HVACMODE = {value: key for key, value in HA_TO_S21_HVACMODE.items()}

S21_TO_HA_HVACACTION = {
    BlS21HVACAction.COOLING: HVACAction.COOLING,
    BlS21HVACAction.FAN: HVACAction.FAN,
    BlS21HVACAction.HEATING: HVACAction.HEATING,
    BlS21HVACAction.IDLE: HVACAction.IDLE,
    BlS21HVACAction.OFF: HVACAction.OFF,
}

S21_TO_HA_FAN_MODE = {1: FAN_LOW, 2: FAN_MEDIUM, 3: FAN_HIGH, 255: "custom"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Blauberg S21 climate entity."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities([BlS21ClimateEntity(coordinator, config_entry)])


class BlS21ClimateEntity(BlaubergS21Entity, ClimateEntity):
    """Representation of a Blauberg S21 climate feature."""

    _attr_translation_key = "s21climate"

    @property
    def name(self) -> str | None:
        if self._device:
            return self._device.name
        return None

    @property
    def unique_id(self) -> str | None:
        return self.base_unique_id

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    @property
    def precision(self) -> float | None:
        if self._device:
            return self._device.precision
        return None

    @property
    def current_temperature(self) -> float | None:
        if self._device:
            return self._device.current_temperature
        return None

    @property
    def target_temperature(self) -> float | None:
        if self._device:
            return self._device.target_temperature
        return None

    @property
    def target_temperature_step(self) -> float | None:
        if self._device:
            return self._device.target_temperature_step
        return None

    @property
    def max_temp(self) -> float | None:
        if self._device:
            return self._device.max_temp
        return None

    @property
    def min_temp(self) -> float | None:
        if self._device:
            return self._device.min_temp
        return None

    @property
    def current_humidity(self) -> float | None:
        if self._device:
            return self._device.current_humidity
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        if self._device:
            return S21_TO_HA_HVACMODE.get(self._device.hvac_mode)
        return None

    @property
    def hvac_action(self) -> HVACAction | None:
        if self._device:
            return S21_TO_HA_HVACACTION.get(self._device.hvac_action)
        return None

    @property
    def hvac_modes(self) -> list[HVACMode] | None:
        if self._device:
            return [
                S21_TO_HA_HVACMODE[mode]
                for mode in self._device.hvac_modes
                if mode in S21_TO_HA_HVACMODE
            ]
        return None

    @property
    def fan_mode(self) -> str | None:
        if self._device:
            if self._device.max_fan_level == 3:
                return S21_TO_HA_FAN_MODE.get(
                    self._device.fan_mode, str(self._device.fan_mode)
                )
            return str(self._device.fan_mode)
        return None

    @property
    def fan_modes(self) -> list[str] | None:
        if self._device:
            if self._device.max_fan_level == 3:
                return [
                    S21_TO_HA_FAN_MODE.get(mode, str(mode))
                    for mode in self._device.fan_modes
                ]
            return [str(mode) for mode in self._device.fan_modes]
        return None

    @property
    def supported_features(self) -> ClimateEntityFeature:
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    @property
    def icon(self) -> str:
        if self._device:
            if not self._device.available:
                return "mdi:lan-disconnect"
            if self._device.is_boosting:
                return "mdi:fan-plus"
            if self._device.hvac_action == BlS21HVACAction.OFF:
                return "mdi:fan-off"
            if self._device.hvac_action == BlS21HVACAction.IDLE:
                return "mdi:fan-remove"
            if self._device.max_fan_level == 3:
                if self._device.fan_mode == 1:
                    return "mdi:fan-speed-1"
                if self._device.fan_mode == 2:
                    return "mdi:fan-speed-2"
                if self._device.fan_mode == 3:
                    return "mdi:fan-speed-3"
            if self._device.hvac_action == BlS21HVACAction.COOLING:
                return "mdi:fan-chevron-down"
            if self._device.hvac_action == BlS21HVACAction.HEATING:
                return "mdi:fan-chevron-up"
            if self._device.hvac_action == BlS21HVACAction.FAN:
                return "mdi:fan"
        return "mdi:fan"

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode and refresh the coordinated state."""
        if hvac_mode not in HA_TO_S21_HVACMODE:
            return
        await self.coordinator.client.set_hvac_mode(HA_TO_S21_HVACMODE[hvac_mode])
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode and record confirmed changes in the logbook."""
        previous_fan_mode = self.fan_mode
        int_fan_mode = (
            255
            if fan_mode == "custom"
            else 1
            if fan_mode == FAN_LOW
            else 2
            if fan_mode == FAN_MEDIUM
            else 3
            if fan_mode == FAN_HIGH
            else int(fan_mode)
        )
        await self.coordinator.client.set_fan_mode(int_fan_mode)
        await self.coordinator.async_request_refresh()

        current_fan_mode = self.fan_mode
        if (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.hass
            and self.entity_id
            and previous_fan_mode is not None
            and current_fan_mode is not None
            and previous_fan_mode != current_fan_mode
        ):
            self.hass.bus.async_fire(
                "logbook_entry",
                {
                    "name": self.name or self._config_entry.title,
                    "message": f"Fan mode changed: {previous_fan_mode} -> {current_fan_mode}",
                    "entity_id": self.entity_id,
                    "domain": DOMAIN,
                },
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature and refresh the coordinated state."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator.client.set_temperature(int(temperature))
            await self.coordinator.async_request_refresh()

    async def async_reset_filter_change_timer(self) -> None:
        """Reset the filter timer and refresh the coordinated state."""
        await self.coordinator.client.reset_filter_change_timer()
        await self.coordinator.async_request_refresh()

    async def async_reset_alarm(self) -> None:
        """Reset alarms and refresh the coordinated state."""
        await self.coordinator.client.reset_alarm()
        await self.coordinator.async_request_refresh()
