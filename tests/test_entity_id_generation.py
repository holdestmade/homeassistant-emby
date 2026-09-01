"""Regression tests for generated entity IDs.

Home Assistant composes entity IDs for entities that set
`has_entity_name = True`:

* entities whose name is None are named after their device
* entities with a name become "<device name> <entity name>"

Both `EmbyEntity` and the server buttons used to override
`suggested_object_id` to force the optional 'Emby' prefix into the entity
ID. Home Assistant treats that value as an `object_id_base` and prefixes it
with the device name, so the prefix was applied twice and every newly
discovered device produced doubled IDs:

    media_player.test_player_test_player
    button.server_1_emby_server_1_refresh_library

The prefix already lives in the device name, so the overrides were both
redundant and harmful. These tests pin the IDs Home Assistant actually
generates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.embymedia.const import (
    CONF_API_KEY,
    CONF_PREFIX_MEDIA_PLAYER,
    CONF_PREFIX_NOTIFY,
    CONF_PREFIX_REMOTE,
    CONF_VERIFY_SSL,
    DOMAIN,
)

from .conftest import add_coordinator_mocks

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

SESSION = {
    "Id": "session-123",
    "DeviceId": "device-123",
    "DeviceName": "Living Room",
    "Client": "Emby Theater",
    "UserName": "TestUser",
    "UserId": "user-123",
    "PlayableMediaTypes": ["Audio", "Video"],
    "SupportsRemoteControl": True,
}


async def _setup(hass: HomeAssistant, options: dict[str, bool]) -> None:
    """Set up the integration with one remote-controllable session."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Server",
        data={
            CONF_HOST: "emby.local",
            CONF_PORT: 8096,
            CONF_SSL: False,
            CONF_API_KEY: "test-api-key",
            CONF_VERIFY_SSL: True,
        },
        options=options,
        unique_id="test-server-id",
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.embymedia.EmbyClient", autospec=True) as client_class,
        patch(
            "custom_components.embymedia.coordinator.EmbyDataUpdateCoordinator"
            ".async_setup_websocket",
            new_callable=AsyncMock,
        ),
    ):
        client = client_class.return_value
        client.async_validate_connection = AsyncMock(return_value=True)
        client.async_get_server_info = AsyncMock(
            return_value={
                "Id": "test-server-id",
                "ServerName": "Test Server",
                "Version": "4.9.0.0",
            }
        )
        client.async_get_sessions = AsyncMock(return_value=[SESSION])
        client.get_image_url.return_value = "http://emby.local/image.jpg"
        add_coordinator_mocks(client)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


class TestEntityIdsAreNotDoubled:
    """Entity IDs must contain the device name exactly once."""

    @pytest.mark.asyncio
    async def test_session_entity_ids_with_prefix_enabled(self, hass: HomeAssistant) -> None:
        """Prefixed device name is used once, not twice."""
        await _setup(
            hass,
            {
                CONF_PREFIX_MEDIA_PLAYER: True,
                CONF_PREFIX_NOTIFY: True,
                CONF_PREFIX_REMOTE: True,
            },
        )

        assert hass.states.get("media_player.emby_living_room") is not None
        assert hass.states.get("media_player.emby_living_room_emby_living_room") is None

    @pytest.mark.asyncio
    async def test_session_entity_ids_with_prefix_disabled(self, hass: HomeAssistant) -> None:
        """Unprefixed device name is used once, not twice."""
        await _setup(
            hass,
            {
                CONF_PREFIX_MEDIA_PLAYER: False,
                CONF_PREFIX_NOTIFY: False,
                CONF_PREFIX_REMOTE: False,
            },
        )

        assert hass.states.get("media_player.living_room") is not None
        assert hass.states.get("media_player.living_room_living_room") is None

    @pytest.mark.asyncio
    async def test_server_button_entity_ids(self, hass: HomeAssistant) -> None:
        """Buttons are "<server device name> <button name>", not doubled."""
        await _setup(hass, {})

        assert hass.states.get("button.test_server_refresh_library") is not None
        assert hass.states.get("button.test_server_run_library_scan") is not None
        assert hass.states.get("button.test_server_emby_test_server_refresh_library") is None

    @pytest.mark.asyncio
    async def test_no_entity_id_repeats_its_device_name(self, hass: HomeAssistant) -> None:
        """No Emby entity ID may repeat the device name twice.

        A generic guard: catches the doubling on every platform, including
        any added later.
        """
        await _setup(hass, {})

        doubled = [
            state.entity_id
            for state in hass.states.async_all()
            if state.entity_id.startswith(("media_player.", "button.", "remote.", "notify."))
            and _repeats_a_segment(state.entity_id)
        ]

        assert doubled == []


def _repeats_a_segment(entity_id: str) -> bool:
    """Return True if the object id repeats its leading words verbatim."""
    object_id = entity_id.split(".", 1)[1]
    parts = object_id.split("_")
    return any(parts[:size] == parts[size : size * 2] for size in range(1, len(parts) // 2 + 1))
