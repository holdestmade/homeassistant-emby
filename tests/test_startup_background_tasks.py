"""Regression tests for Home Assistant startup blocking.

Long-lived coordinator loops (health check, WebSocket receive) were
previously created with ``hass.async_create_task``. Home Assistant's
bootstrap waits for all tracked tasks before completing startup, so those
never-ending loops held bootstrap open until its timeout, delaying every
restart by many minutes:

    Setup timed out for bootstrap waiting on
    EmbyDataUpdateCoordinator._schedule_health_check.<locals>._health_check_loop()
    EmbyDataUpdateCoordinator._async_websocket_receive_loop()

They must be created with ``hass.async_create_background_task`` instead,
which is excluded from the startup wait (and still cancelled at shutdown).

``hass.async_block_till_done()`` waits for tracked tasks exactly like the
bootstrap wrap-up does, so these tests assert it completes promptly while
the loops are still running.

Related: troykelly/homeassistant-emby issues #323 and #331.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.embymedia.coordinator import EmbyDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


BLOCK_TILL_DONE_TIMEOUT = 5.0


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock Emby client."""
    client = MagicMock()
    client.host = "emby.local"
    client.port = 8096
    client.api_key = "test-key"
    client.ssl = False
    client.async_get_sessions = AsyncMock(return_value=[])
    client.async_ping = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.options = {}
    return entry


def _make_coordinator(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MagicMock,
) -> EmbyDataUpdateCoordinator:
    """Create a coordinator for testing."""
    return EmbyDataUpdateCoordinator(
        hass=hass,
        client=mock_client,
        server_id="test-server",
        server_name="Test Server",
        config_entry=mock_config_entry,
    )


class TestHealthCheckLoopIsBackgroundTask:
    """The health check loop must not block HA startup."""

    @pytest.mark.asyncio
    async def test_health_check_loop_does_not_block_startup(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """block_till_done must complete while the health check loop runs.

        Bootstrap waits on tracked tasks the same way block_till_done
        does. If the never-ending health check loop were a tracked task,
        this would hang until the timeout below.
        """
        coordinator = _make_coordinator(hass, mock_client, mock_config_entry)

        # Reach the stable state that starts the health check loop
        coordinator._polling_disabled = True
        coordinator._schedule_health_check()

        task = coordinator._health_check_task
        assert task is not None
        assert not task.done()

        # Must complete promptly: background tasks are not waited on
        await asyncio.wait_for(hass.async_block_till_done(), timeout=BLOCK_TILL_DONE_TIMEOUT)

        # The loop is still alive afterwards (it was not waited out)
        assert not task.done()

        # Clean up
        task.cancel()

    @pytest.mark.asyncio
    async def test_health_check_task_created_as_background_task(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """The health check loop is created via async_create_background_task."""
        coordinator = _make_coordinator(hass, mock_client, mock_config_entry)

        with patch.object(
            hass, "async_create_background_task", wraps=hass.async_create_background_task
        ) as mock_bg:
            coordinator._polling_disabled = True
            coordinator._schedule_health_check()

        mock_bg.assert_called_once()

        task = coordinator._health_check_task
        assert task is not None
        task.cancel()


class TestWebSocketReceiveLoopIsBackgroundTask:
    """The WebSocket receive loop must not block HA startup."""

    @pytest.mark.asyncio
    async def test_receive_loop_does_not_block_startup(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """block_till_done must complete while the receive loop runs."""
        coordinator = _make_coordinator(hass, mock_client, mock_config_entry)

        # WebSocket whose receive loop never returns (like a live connection)
        forever = asyncio.Event()

        mock_websocket = MagicMock()
        mock_websocket.async_connect = AsyncMock()
        mock_websocket.async_subscribe_sessions = AsyncMock()
        mock_websocket.async_run_receive_loop = AsyncMock(side_effect=forever.wait)
        mock_websocket.async_stop_reconnect_loop = AsyncMock()

        with patch(
            "custom_components.embymedia.coordinator.EmbyWebSocket",
            return_value=mock_websocket,
        ):
            await coordinator.async_setup_websocket(MagicMock())

        task = coordinator._websocket_receive_task
        assert task is not None
        assert not task.done()

        # Must complete promptly: background tasks are not waited on
        await asyncio.wait_for(hass.async_block_till_done(), timeout=BLOCK_TILL_DONE_TIMEOUT)

        # The loop is still alive afterwards (it was not waited out)
        assert not task.done()

        # Clean up
        await coordinator.async_shutdown_websocket()

    @pytest.mark.asyncio
    async def test_receive_loop_created_as_background_task(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
    ) -> None:
        """The receive loop is created via async_create_background_task."""
        coordinator = _make_coordinator(hass, mock_client, mock_config_entry)

        forever = asyncio.Event()

        mock_websocket = MagicMock()
        mock_websocket.async_connect = AsyncMock()
        mock_websocket.async_subscribe_sessions = AsyncMock()
        mock_websocket.async_run_receive_loop = AsyncMock(side_effect=forever.wait)
        mock_websocket.async_stop_reconnect_loop = AsyncMock()

        with (
            patch(
                "custom_components.embymedia.coordinator.EmbyWebSocket",
                return_value=mock_websocket,
            ),
            patch.object(
                hass,
                "async_create_background_task",
                wraps=hass.async_create_background_task,
            ) as mock_bg,
        ):
            await coordinator.async_setup_websocket(MagicMock())

        mock_bg.assert_called_once()

        await coordinator.async_shutdown_websocket()
