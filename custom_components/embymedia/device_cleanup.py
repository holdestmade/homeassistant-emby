"""Removal of stale Emby client devices from the device registry."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry

    from .const import EmbyConfigEntry
    from .coordinator import EmbyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_session_coordinator(entry: EmbyConfigEntry) -> EmbyDataUpdateCoordinator | None:
    """Return the entry's session coordinator, or None if it isn't loaded."""
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is None:
        return None
    coordinator: EmbyDataUpdateCoordinator = runtime_data.session_coordinator
    return coordinator


def _emby_ids(device_entry: DeviceEntry) -> set[str]:
    """Return the Emby identifiers of a device registry entry."""
    return {identifier for domain, identifier in device_entry.identifiers if domain == DOMAIN}


@callback
def async_can_remove_client_device(entry: EmbyConfigEntry, device_entry: DeviceEntry) -> bool:
    """Check whether a device can be removed, and prepare for its removal.

    A device can be removed when it is an Emby client (not the Emby server)
    without an active session. When it can, the platforms are told to forget
    it so its entities are re-created if the client starts a session again.

    Args:
        entry: Config entry the device belongs to.
        device_entry: Device to check.

    Returns:
        True if the device may be removed.
    """
    coordinator = _get_session_coordinator(entry)
    emby_ids = _emby_ids(device_entry)

    # The config entry's unique id is the Emby server id; fall back to it
    # when the entry isn't loaded (e.g. the server is offline).
    server_id = coordinator.server_id if coordinator is not None else entry.unique_id

    if server_id in emby_ids:
        _LOGGER.warning(
            "The Emby server device %s can't be deleted; remove the integration instead",
            device_entry.name,
        )
        return False

    if coordinator is None:
        # Not loaded, so nothing is going to re-create the device.
        return True

    active = [device_id for device_id in emby_ids if coordinator.get_session(device_id)]
    if active:
        _LOGGER.warning(
            "Emby device %s has an active session and can't be deleted. "
            "Close the client (or add it to the ignored devices option) first",
            device_entry.name_by_user or device_entry.name,
        )
        return False

    for device_id in emby_ids:
        coordinator.async_notify_device_removed(device_id)
    return True


@callback
def async_remove_inactive_client_devices(hass: HomeAssistant) -> list[str]:
    """Remove every Emby client device that has no active session.

    Only config entries that are loaded are cleaned up, as their session
    data is needed to tell which clients are still active.

    Args:
        hass: Home Assistant instance.

    Returns:
        Names of the devices that were removed.
    """
    device_registry = dr.async_get(hass)
    removed: list[str] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        coordinator = _get_session_coordinator(entry)
        if coordinator is None or coordinator.data is None:
            # No session data yet: can't tell what is active, so skip.
            continue

        for device_entry in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
            emby_ids = _emby_ids(device_entry)
            if not emby_ids or coordinator.server_id in emby_ids:
                continue
            if any(coordinator.get_session(device_id) for device_id in emby_ids):
                continue

            for device_id in emby_ids:
                coordinator.async_notify_device_removed(device_id)
            device_registry.async_update_device(
                device_entry.id, remove_config_entry_id=entry.entry_id
            )
            removed.append(device_entry.name_by_user or device_entry.name or device_entry.id)

    if removed:
        _LOGGER.info("Removed %d inactive Emby device(s): %s", len(removed), ", ".join(removed))
    else:
        _LOGGER.info("No inactive Emby devices to remove")
    return removed


__all__ = ["async_can_remove_client_device", "async_remove_inactive_client_devices"]
