"""Data update coordinator for the Blauberg S21 integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pybls21.client import S21Client
from pybls21.models import ClimateDevice

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BlaubergS21DataUpdateCoordinator(DataUpdateCoordinator[ClimateDevice]):
    """Coordinate a single periodic poll of a Blauberg S21 device."""

    def __init__(self, hass: HomeAssistant, client: S21Client) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )
        self.client = client

    async def _async_update_data(self) -> ClimateDevice:
        """Poll the device and return its latest state."""
        try:
            await self.client.poll()
        except Exception as err:
            raise UpdateFailed("Error communicating with Blauberg S21") from err

        if self.client.device is None:
            raise UpdateFailed("Blauberg S21 returned no device state")
        return self.client.device
