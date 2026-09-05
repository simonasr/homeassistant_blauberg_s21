"""Tests for the shared Blauberg S21 coordinator."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator


async def test_coordinator_polls_once_and_returns_device(hass) -> None:
    """A refresh performs one client poll and shares its device data."""
    device = SimpleNamespace(available=True)
    client = SimpleNamespace(device=device, poll=AsyncMock())
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)

    await coordinator.async_refresh()

    client.poll.assert_awaited_once()
    assert coordinator.data is device
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator.always_update is False


async def test_coordinator_marks_failed_poll_as_update_failed(hass) -> None:
    """Polling failures are exposed to Home Assistant as coordinator failures."""
    client = SimpleNamespace(
        device=None, poll=AsyncMock(side_effect=OSError("offline"))
    )
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)

    with pytest.raises(UpdateFailed, match="Error communicating") as err:
        await coordinator._async_update_data()

    assert "offline" not in str(err.value)
