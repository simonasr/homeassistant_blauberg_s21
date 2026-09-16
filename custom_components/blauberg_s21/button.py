"""Button controls for the Blauberg S21 integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import BlaubergS21DataUpdateCoordinator
from .entity import BlaubergS21Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BlaubergS21ButtonEntityDescription(ButtonEntityDescription):
    """Describe a Blauberg S21 button command."""

    command: str


BUTTON_DESCRIPTIONS = (
    BlaubergS21ButtonEntityDescription(
        key="reset_filter_timer",
        translation_key="reset_filter_timer",
        entity_category=EntityCategory.CONFIG,
        command="reset_filter_change_timer",
    ),
    BlaubergS21ButtonEntityDescription(
        key="reset_alarms",
        translation_key="reset_alarms",
        entity_category=EntityCategory.CONFIG,
        command="reset_alarm",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blauberg S21 button controls."""
    coordinator: BlaubergS21DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        [
            BlaubergS21Button(coordinator, config_entry, description)
            for description in BUTTON_DESCRIPTIONS
        ]
    )


class BlaubergS21Button(BlaubergS21Entity, ButtonEntity):
    """Run a stateless Blauberg S21 maintenance command."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlaubergS21DataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: BlaubergS21ButtonEntityDescription,
    ) -> None:
        """Initialize a maintenance button."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        if base_unique_id := self.base_unique_id:
            self._attr_unique_id = f"{base_unique_id}_{description.key}"

    async def async_press(self) -> None:
        """Run the command and refresh coordinated state."""
        command = getattr(self.coordinator.client, self.entity_description.command)
        await command()
        await self.coordinator.async_request_refresh()
