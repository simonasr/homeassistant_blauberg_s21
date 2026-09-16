"""Select controls for the Blauberg S21 integration."""

from __future__ import annotations

from typing import ClassVar

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pybls21.models import HeatExchangerMode, HeatExchangerType

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0

OPTION_AUTO = "auto"
OPTION_ROTOR_ON = "rotor_on"
OPTION_ROTOR_OFF = "rotor_off"

OPTION_TO_MODE = {
    OPTION_AUTO: HeatExchangerMode.AUTO,
    OPTION_ROTOR_ON: HeatExchangerMode.ROTOR_ON,
    OPTION_ROTOR_OFF: HeatExchangerMode.ROTOR_OFF,
}
MODE_TO_OPTION = {mode: option for option, mode in OPTION_TO_MODE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up controls supported by this heat exchanger."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    if (
        coordinator.data is not None
        and coordinator.data.heat_exchanger_type is HeatExchangerType.ROTARY_DISCRETE
    ):
        async_add_entities([BlaubergS21RotorModeSelect(coordinator, config_entry)])


class BlaubergS21RotorModeSelect(BlaubergS21Entity, SelectEntity):
    """Control a discrete rotary heat exchanger."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_options: ClassVar[list[str]] = [
        OPTION_AUTO,
        OPTION_ROTOR_ON,
        OPTION_ROTOR_OFF,
    ]
    _attr_translation_key = "rotor_mode"

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the rotor mode select."""
        super().__init__(coordinator, config_entry)
        if base_unique_id := self.base_unique_id:
            self._attr_unique_id = f"{base_unique_id}_rotor_mode"

    @property
    def current_option(self) -> str | None:
        """Return the confirmed rotor mode."""
        if self._device is None:
            return None
        return MODE_TO_OPTION.get(self._device.heat_exchanger_mode)

    async def async_select_option(self, option: str) -> None:
        """Set the rotor mode and refresh the coordinated state."""
        try:
            mode = OPTION_TO_MODE[option]
        except KeyError as err:
            raise ValueError(f"Unsupported rotor mode option: {option}") from err
        await self.coordinator.client.set_heat_exchanger_mode(mode)
        await self.coordinator.async_request_refresh()
