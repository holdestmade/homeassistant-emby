"""Base entity for Emby integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PREFIX_MEDIA_PLAYER,
    DEFAULT_PREFIX_MEDIA_PLAYER,
    DOMAIN,
)

if TYPE_CHECKING:
    from .coordinator import EmbyDataUpdateCoordinator
    from .models import EmbySession

# Home Assistant replaced DeviceInfo's `via_device` (an identifier tuple) with
# `via_device_id` (the parent device's registry id). `via_device` still works
# but is reported as deprecated and stops working in HA 2027.8.0, while
# `via_device_id` is rejected outright by older versions - device info keys are
# passed straight through to `async_get_or_create` as keyword arguments. Detect
# which one this Home Assistant understands so the integration keeps working on
# the minimum supported version (2025.11.3) as well as current releases.
_SUPPORTS_VIA_DEVICE_ID = "via_device_id" in DeviceInfo.__annotations__


class EmbyEntity(CoordinatorEntity["EmbyDataUpdateCoordinator"]):
    """Base class for Emby entities.

    Provides common functionality including:
    - Device info generation
    - Unique ID management
    - Availability based on session presence
    - Session data access

    Attributes:
        _device_id: The stable device identifier.
        _prefix_key: Config key for entity's prefix toggle.
        _prefix_default: Default value for prefix toggle.
    """

    _attr_has_entity_name = True

    # Subclasses should override these for their specific prefix settings
    _prefix_key: str = CONF_PREFIX_MEDIA_PLAYER
    _prefix_default: bool = DEFAULT_PREFIX_MEDIA_PLAYER

    def __init__(
        self,
        coordinator: EmbyDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: The data update coordinator.
            device_id: The stable device identifier for this entity.
        """
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def session(self) -> EmbySession | None:
        """Return the current session data.

        Returns:
            The session if available, None otherwise.
        """
        result: EmbySession | None = self.coordinator.get_session(self._device_id)
        return result

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        Entity is available when:
        - Coordinator has data
        - Session exists in coordinator data
        """
        return self.coordinator.last_update_success and self.session is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information.

        Phase 11: Uses _get_device_name to support optional 'Emby' prefix.

        Returns:
            DeviceInfo for device registry.
        """
        session = self.session
        device_name = self._get_device_name(self._prefix_key, self._prefix_default)

        if session is None:
            # Fallback device info when session not available
            device_info = DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
                name=device_name,
                manufacturer="Emby",
            )
        else:
            device_info = DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
                name=device_name,
                manufacturer="Emby",
                model=session.client_name,
                sw_version=session.app_version,
            )

        self._add_via_device(device_info)
        return device_info

    def _add_via_device(self, device_info: DeviceInfo) -> None:
        """Link this device to the Emby server device.

        Uses `via_device_id` where Home Assistant supports it and falls back
        to the deprecated `via_device` identifier tuple on older versions.
        Neither key is set when the server device id is not known yet, which
        leaves the device unlinked rather than failing to register it.

        Args:
            device_info: Device info to add the server link to.
        """
        # Written through a plain mapping: only one of these keys exists in
        # any given Home Assistant version's DeviceInfo definition.
        keys = cast("dict[str, object]", device_info)

        if not _SUPPORTS_VIA_DEVICE_ID:
            keys["via_device"] = (DOMAIN, self.coordinator.server_id)
            return

        server_device_id = self.coordinator.server_device_id
        if server_device_id is not None:
            keys["via_device_id"] = server_device_id

    @property
    def unique_id(self) -> str:
        """Return unique ID for the entity.

        Uses device_id which persists across session reconnections.
        """
        return f"{self.coordinator.server_id}_{self._device_id}"

    def _get_device_name(self, prefix_key: str, prefix_default: bool) -> str:
        """Get device name with optional 'Emby' prefix.

        Phase 11: Allows users to toggle 'Emby' prefix in device names via options.

        Args:
            prefix_key: The options key for this entity's prefix toggle
                       (e.g., CONF_PREFIX_MEDIA_PLAYER)
            prefix_default: The default value for the prefix toggle

        Returns:
            Device name with or without 'Emby' prefix based on user setting.
        """
        # Get the prefix toggle from options (with fallback to default)
        use_prefix: bool = self.coordinator.config_entry.options.get(prefix_key, prefix_default)

        session = self.session
        if session is not None:
            device_name = session.device_name
        else:
            # Fallback to short device ID
            device_name = f"Client {self._device_id[:8]}"

        if use_prefix:
            return f"Emby {device_name}"
        return device_name


__all__ = ["EmbyEntity"]
