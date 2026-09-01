"""Tests for config entry migration.

Version 2 replaced four per-platform name prefix options with one device
setting. The media_player, notify and remote entities for a client all
attach to the same device, so at most one of those three could ever take
effect - whichever platform registered last won - and `prefix_button`
applied to the shared server device, whose name the integration never sets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.embymedia import async_migrate_entry
from custom_components.embymedia.const import (
    CONF_API_KEY,
    CONF_PREFIX_BUTTON,
    CONF_PREFIX_DEVICE_NAMES,
    CONF_PREFIX_MEDIA_PLAYER,
    CONF_PREFIX_NOTIFY,
    CONF_PREFIX_REMOTE,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _entry(hass: HomeAssistant, options: dict[str, object], version: int = 1):
    """Create a config entry at the given schema version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "emby.local", "port": 8096, CONF_API_KEY: "key"},
        options=options,
        unique_id="server-1",
        version=version,
    )
    entry.add_to_hass(hass)
    return entry


class TestPrefixOptionMigration:
    """Version 1 entries carry their prefix setting across."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", [True, False])
    async def test_media_player_setting_is_carried_over(
        self, hass: HomeAssistant, enabled: bool
    ) -> None:
        """The media_player value becomes the device setting."""
        entry = _entry(
            hass,
            {
                CONF_PREFIX_MEDIA_PLAYER: enabled,
                CONF_PREFIX_NOTIFY: not enabled,
                CONF_PREFIX_REMOTE: not enabled,
                CONF_PREFIX_BUTTON: not enabled,
            },
        )

        assert await async_migrate_entry(hass, entry) is True

        assert entry.version == 2
        assert entry.options[CONF_PREFIX_DEVICE_NAMES] is enabled

    @pytest.mark.asyncio
    async def test_legacy_keys_are_removed(self, hass: HomeAssistant) -> None:
        """The retired keys do not linger in options."""
        entry = _entry(
            hass,
            {
                CONF_PREFIX_MEDIA_PLAYER: True,
                CONF_PREFIX_NOTIFY: True,
                CONF_PREFIX_REMOTE: True,
                CONF_PREFIX_BUTTON: True,
            },
        )

        await async_migrate_entry(hass, entry)

        for key in (
            CONF_PREFIX_MEDIA_PLAYER,
            CONF_PREFIX_NOTIFY,
            CONF_PREFIX_REMOTE,
            CONF_PREFIX_BUTTON,
        ):
            assert key not in entry.options

    @pytest.mark.asyncio
    async def test_unrelated_options_are_preserved(self, hass: HomeAssistant) -> None:
        """Migration touches only the prefix options."""
        entry = _entry(
            hass,
            {
                "scan_interval": 25,
                "enable_discovery_sensors": False,
                CONF_PREFIX_MEDIA_PLAYER: False,
            },
        )

        await async_migrate_entry(hass, entry)

        assert entry.options["scan_interval"] == 25
        assert entry.options["enable_discovery_sensors"] is False
        assert entry.options[CONF_PREFIX_DEVICE_NAMES] is False

    @pytest.mark.asyncio
    async def test_entry_without_prefix_options_defaults_to_enabled(
        self, hass: HomeAssistant
    ) -> None:
        """An entry that never set a prefix gets the default."""
        entry = _entry(hass, {"scan_interval": 10})

        await async_migrate_entry(hass, entry)

        assert entry.version == 2
        assert entry.options[CONF_PREFIX_DEVICE_NAMES] is True

    @pytest.mark.asyncio
    async def test_current_version_is_left_alone(self, hass: HomeAssistant) -> None:
        """A version 2 entry is already current."""
        entry = _entry(hass, {CONF_PREFIX_DEVICE_NAMES: False}, version=2)

        assert await async_migrate_entry(hass, entry) is True

        assert entry.version == 2
        assert entry.options[CONF_PREFIX_DEVICE_NAMES] is False

    @pytest.mark.asyncio
    async def test_future_version_is_refused(self, hass: HomeAssistant) -> None:
        """A downgrade cannot be migrated and must not be silently accepted."""
        entry = _entry(hass, {}, version=3)

        assert await async_migrate_entry(hass, entry) is False


class TestMigratedEntryDrivesDeviceNames:
    """The migrated option is what the entities actually read."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", [True, False])
    async def test_device_name_follows_migrated_option(
        self, hass: HomeAssistant, enabled: bool
    ) -> None:
        """Device naming honours the value carried over by migration."""
        from unittest.mock import MagicMock

        from custom_components.embymedia.entity import EmbyEntity

        entry = _entry(hass, {CONF_PREFIX_MEDIA_PLAYER: enabled})
        await async_migrate_entry(hass, entry)

        session = MagicMock(spec_set=["device_id", "device_name", "client_name", "app_version"])
        session.device_name = "Living Room"
        session.client_name = "Emby Theater"
        session.app_version = "1.0"

        coordinator = MagicMock()
        coordinator.config_entry = entry
        coordinator.get_session.return_value = session
        coordinator.server_id = "server-1"
        coordinator.server_device_id = "dev-1"

        entity = EmbyEntity(coordinator=coordinator, device_id="device-1")

        expected = "Emby Living Room" if enabled else "Living Room"
        assert entity.device_info["name"] == expected
