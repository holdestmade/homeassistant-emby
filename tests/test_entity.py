"""Tests for Emby base entity."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.embymedia.const import DOMAIN
from custom_components.embymedia.entity import _SUPPORTS_VIA_DEVICE_ID

if TYPE_CHECKING:
    from homeassistant.helpers.device_registry import DeviceInfo


def assert_linked_to_server(device_info: DeviceInfo) -> None:
    """Assert the device is linked to the Emby server device.

    Home Assistant replaced `via_device` with `via_device_id`; which key is
    used depends on the running Home Assistant version.
    """
    keys = dict(device_info)
    if _SUPPORTS_VIA_DEVICE_ID:
        assert keys["via_device_id"] == "server-device-registry-id"
        assert "via_device" not in keys
    else:
        assert keys["via_device"] == (DOMAIN, "server-123")
        assert "via_device_id" not in keys


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock EmbySession."""
    session = MagicMock(spec_set=["device_id", "device_name", "client_name", "app_version"])
    session.device_id = "device-abc-123"
    session.device_name = "Living Room TV"
    session.client_name = "Emby Theater"
    session.app_version = "4.9.2.0"
    return session


@pytest.fixture
def mock_coordinator(hass: HomeAssistant, mock_session: MagicMock) -> MagicMock:
    """Create a mock coordinator."""
    from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES

    coordinator = MagicMock()
    coordinator.server_id = "server-123"
    coordinator.server_device_id = "server-device-registry-id"
    coordinator.server_name = "My Emby Server"
    coordinator.last_update_success = True
    coordinator.data = {"device-abc-123": mock_session}
    coordinator.get_session = MagicMock(return_value=mock_session)
    # Phase 11: Add config_entry with default prefix settings (enabled by default)
    mock_config_entry = MagicMock()
    mock_config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
    coordinator.config_entry = mock_config_entry
    return coordinator


class TestEmbyEntityInit:
    """Test EmbyEntity initialization."""

    def test_entity_init(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity initializes with correct attributes."""
        from custom_components.embymedia.entity import EmbyEntity

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity._device_id == "device-abc-123"
        assert entity.coordinator is mock_coordinator

    def test_entity_has_entity_name_attribute(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity has _attr_has_entity_name = True."""
        from custom_components.embymedia.entity import EmbyEntity

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity._attr_has_entity_name is True


class TestEmbyEntitySession:
    """Test EmbyEntity session property."""

    def test_session_returns_session_from_coordinator(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test session property returns session from coordinator."""
        from custom_components.embymedia.entity import EmbyEntity

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity.session is mock_session
        mock_coordinator.get_session.assert_called_once_with("device-abc-123")


class TestEmbyEntityAvailability:
    """Test EmbyEntity availability."""

    def test_available_when_session_exists_and_update_success(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test entity is available when session exists and coordinator succeeded."""
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.last_update_success = True
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity.available is True

    def test_unavailable_when_session_missing(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test entity is unavailable when session doesn't exist."""
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.last_update_success = True
        mock_coordinator.get_session.return_value = None

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-xyz-999",
        )

        assert entity.available is False

    def test_unavailable_when_coordinator_failed(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test entity is unavailable when coordinator failed."""
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.last_update_success = False
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity.available is False


class TestEmbyEntityDeviceInfo:
    """Test EmbyEntity device info (Phase 11 - with prefix support)."""

    def test_device_info_with_session_and_prefix_enabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test device info with 'Emby' prefix when session is available and prefix enabled."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Ensure prefix is enabled (default)
        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        device_info = entity.device_info

        assert device_info["identifiers"] == {(DOMAIN, "device-abc-123")}
        assert device_info["name"] == "Emby Living Room TV"  # Phase 11: Prefixed
        assert device_info["manufacturer"] == "Emby"
        assert device_info["model"] == "Emby Theater"
        assert device_info["sw_version"] == "4.9.2.0"
        assert_linked_to_server(device_info)

    def test_device_info_with_session_and_prefix_disabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test device info without prefix when prefix disabled."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Disable prefix
        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: False}
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        device_info = entity.device_info

        assert device_info["identifiers"] == {(DOMAIN, "device-abc-123")}
        assert device_info["name"] == "Living Room TV"  # No prefix
        assert device_info["manufacturer"] == "Emby"
        assert device_info["model"] == "Emby Theater"
        assert device_info["sw_version"] == "4.9.2.0"
        assert_linked_to_server(device_info)

    def test_device_info_without_session(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test device info fallback when session is not available."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.get_session.return_value = None

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        device_info = entity.device_info

        assert device_info["identifiers"] == {(DOMAIN, "device-abc-123")}
        assert device_info["name"] == "Emby Client device-a"  # Fallback with prefix
        assert device_info["manufacturer"] == "Emby"
        assert "model" not in device_info
        assert "sw_version" not in device_info
        assert_linked_to_server(device_info)


class TestEmbyEntityUniqueId:
    """Test EmbyEntity unique_id."""

    def test_unique_id_format(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test unique_id combines server_id and device_id."""
        from custom_components.embymedia.entity import EmbyEntity

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        assert entity.unique_id == "server-123_device-abc-123"


class TestEmbyEntityDeviceNameHelper:
    """Test _get_device_name helper for entity prefix support (Phase 11)."""

    def test_get_device_name_with_prefix_enabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test device name prefixed with 'Emby' when toggle is ON."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Setup mock config entry with prefix enabled
        mock_config_entry = MagicMock()
        mock_config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.config_entry = mock_config_entry
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        result = entity._get_device_name()

        assert result == "Emby Living Room TV"

    def test_get_device_name_with_prefix_disabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test device name without prefix when toggle is OFF."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Setup mock config entry with prefix disabled
        mock_config_entry = MagicMock()
        mock_config_entry.options = {CONF_PREFIX_DEVICE_NAMES: False}
        mock_coordinator.config_entry = mock_config_entry
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        result = entity._get_device_name()

        assert result == "Living Room TV"

    def test_get_device_name_uses_default_when_option_missing(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test device name uses default when option not set."""
        from custom_components.embymedia.entity import EmbyEntity

        # Setup mock config entry with no prefix option (uses default=True)
        mock_config_entry = MagicMock()
        mock_config_entry.options = {}  # No options set
        mock_coordinator.config_entry = mock_config_entry
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        result = entity._get_device_name()

        # Default is True, so should be prefixed
        assert result == "Emby Living Room TV"

    def test_get_device_name_fallback_when_session_none(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test fallback device name when session is None."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Setup mock config entry with prefix enabled
        mock_config_entry = MagicMock()
        mock_config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.config_entry = mock_config_entry
        mock_coordinator.get_session.return_value = None

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        result = entity._get_device_name()

        # Should use fallback name (first 8 chars of device ID)
        assert result == "Emby Client device-a"

    def test_get_device_name_fallback_without_prefix(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test fallback device name without prefix when toggle is OFF."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        # Setup mock config entry with prefix disabled
        mock_config_entry = MagicMock()
        mock_config_entry.options = {CONF_PREFIX_DEVICE_NAMES: False}
        mock_coordinator.config_entry = mock_config_entry
        mock_coordinator.get_session.return_value = None

        entity = EmbyEntity(
            coordinator=mock_coordinator,
            device_id="device-abc-123",
        )

        result = entity._get_device_name()

        # Should use fallback name without prefix
        assert result == "Client device-a"


class TestEmbyEntityDeviceNaming:
    """Test the device name that entity IDs are derived from.

    These entities set `_attr_name = None` with `has_entity_name = True`, so
    Home Assistant derives the entity ID from the device name. The device
    name carries the optional 'Emby' prefix, so no `suggested_object_id`
    override is needed - and one would actively break things, because Home
    Assistant treats that value as an `object_id_base` and prefixes it with
    the device name again, yielding IDs like
    `media_player.emby_living_room_tv_emby_living_room_tv`.
    """

    def test_no_suggested_object_id_override(self) -> None:
        """EmbyEntity must not override `suggested_object_id`.

        Home Assistant composes the entity ID from the device name; an
        override here is re-prefixed with that same device name.
        """
        from homeassistant.helpers.entity import Entity

        from custom_components.embymedia.entity import EmbyEntity

        assert "suggested_object_id" not in vars(EmbyEntity)
        assert EmbyEntity.suggested_object_id is Entity.suggested_object_id

    def test_device_name_includes_prefix_when_enabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """The device name carries the 'Emby' prefix when enabled."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        assert entity.device_info["name"] == "Emby Living Room TV"

    def test_device_name_excludes_prefix_when_disabled(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """The device name drops the prefix when disabled."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: False}
        mock_coordinator.get_session.return_value = mock_session

        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        assert entity.device_info["name"] == "Living Room TV"

    def test_device_name_falls_back_when_session_none(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
    ) -> None:
        """The device name falls back to a short device id with no session."""
        from custom_components.embymedia.const import CONF_PREFIX_DEVICE_NAMES
        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.config_entry.options = {CONF_PREFIX_DEVICE_NAMES: True}
        mock_coordinator.get_session.return_value = None

        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        assert entity.device_info["name"] == "Emby Client device-a"


class TestEmbyEntityViaDeviceCompatibility:
    """Test the server device link across Home Assistant versions.

    Home Assistant deprecated DeviceInfo's `via_device` (an identifier tuple)
    in favour of `via_device_id` (the parent device's registry id). Using
    `via_device` on a current version logs:

        Detected that custom integration 'embymedia' calls
        `device_registry.async_get_or_create` with a deprecated `via_device`
        parameter; use `via_device_id` instead

    but `via_device_id` is rejected by older versions, because device info
    keys are passed to `async_get_or_create` as keyword arguments. Both
    branches are tested here regardless of the Home Assistant under test.
    """

    def test_uses_via_device_id_when_supported(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Modern Home Assistant gets `via_device_id`, never `via_device`."""
        from unittest.mock import patch

        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.get_session.return_value = mock_session
        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        with patch("custom_components.embymedia.entity._SUPPORTS_VIA_DEVICE_ID", True):
            device_info = dict(entity.device_info)

        assert device_info["via_device_id"] == "server-device-registry-id"
        assert "via_device" not in device_info

    def test_falls_back_to_via_device_when_unsupported(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Older Home Assistant still gets the `via_device` identifier tuple."""
        from unittest.mock import patch

        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.get_session.return_value = mock_session
        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        with patch("custom_components.embymedia.entity._SUPPORTS_VIA_DEVICE_ID", False):
            device_info = dict(entity.device_info)

        assert device_info["via_device"] == (DOMAIN, "server-123")
        assert "via_device_id" not in device_info

    def test_no_link_when_server_device_id_unknown(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """An unknown server device id leaves the device unlinked, not broken.

        Passing `via_device_id=None` would be rejected, so the key is omitted
        entirely and the device still registers.
        """
        from unittest.mock import patch

        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.get_session.return_value = mock_session
        mock_coordinator.server_device_id = None
        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        with patch("custom_components.embymedia.entity._SUPPORTS_VIA_DEVICE_ID", True):
            device_info = dict(entity.device_info)

        assert "via_device_id" not in device_info
        assert "via_device" not in device_info
        assert device_info["identifiers"] == {(DOMAIN, "device-abc-123")}

    def test_device_info_keys_are_accepted_by_device_registry(
        self,
        hass: HomeAssistant,
        mock_coordinator: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Every emitted key must be a real DeviceInfo key for this HA version.

        Entity platforms pass device info straight to `async_get_or_create`
        as keyword arguments, so an unknown key breaks entity registration.
        """
        from homeassistant.helpers.device_registry import DeviceInfo

        from custom_components.embymedia.entity import EmbyEntity

        mock_coordinator.get_session.return_value = mock_session
        entity = EmbyEntity(coordinator=mock_coordinator, device_id="device-abc-123")

        device_info = dict(entity.device_info)

        assert set(device_info) <= set(DeviceInfo.__annotations__)
