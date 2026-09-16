"""Tests for Blauberg S21 maintenance buttons."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.const import EntityCategory

from custom_components.blauberg_s21.button import (
    BUTTON_DESCRIPTIONS,
    BlaubergS21Button,
)
from custom_components.blauberg_s21.coordinator import BlaubergS21DataUpdateCoordinator


@pytest.fixture
def config_entry():
    """Return the config-entry attributes used by buttons."""
    return SimpleNamespace(unique_id="synthetic-device", title="Test unit")


@pytest.fixture
def coordinator(hass):
    """Return a successful coordinator with inspectable maintenance commands."""
    device = SimpleNamespace(
        available=True,
        unique_id="library-device",
        name="Test unit",
        manufacturer="Blauberg",
        model="S21",
        sw_version="test",
    )
    client = SimpleNamespace(
        reset_filter_change_timer=AsyncMock(),
        reset_alarm=AsyncMock(),
    )
    coordinator = BlaubergS21DataUpdateCoordinator(hass, client)
    coordinator.data = device
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_button_metadata(coordinator, config_entry) -> None:
    """Maintenance buttons have stable identities and config categorization."""
    buttons = {
        description.key: BlaubergS21Button(
            coordinator, config_entry, description
        )
        for description in BUTTON_DESCRIPTIONS
    }

    assert set(buttons) == {"reset_filter_timer", "reset_alarms"}
    assert (
        buttons["reset_filter_timer"].unique_id
        == "synthetic-device_reset_filter_timer"
    )
    assert buttons["reset_alarms"].entity_category is EntityCategory.CONFIG


@pytest.mark.parametrize(
    ("key", "client_method"),
    [
        ("reset_filter_timer", "reset_filter_change_timer"),
        ("reset_alarms", "reset_alarm"),
    ],
)
async def test_button_press_runs_command_and_refreshes(
    coordinator, config_entry, key, client_method
) -> None:
    """Each button runs exactly one command and one coordinated refresh."""
    description = next(item for item in BUTTON_DESCRIPTIONS if item.key == key)
    entity = BlaubergS21Button(coordinator, config_entry, description)

    await entity.async_press()

    getattr(coordinator.client, client_method).assert_awaited_once()
    coordinator.async_request_refresh.assert_awaited_once()


async def test_failed_button_command_does_not_refresh(coordinator, config_entry) -> None:
    """A failed maintenance command does not pretend state was refreshed."""
    description = next(
        item for item in BUTTON_DESCRIPTIONS if item.key == "reset_alarms"
    )
    coordinator.client.reset_alarm.side_effect = OSError("write failed")
    entity = BlaubergS21Button(coordinator, config_entry, description)

    with pytest.raises(OSError, match="write failed"):
        await entity.async_press()

    coordinator.async_request_refresh.assert_not_awaited()
