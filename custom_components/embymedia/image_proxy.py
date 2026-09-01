"""Emby image proxy view."""

from __future__ import annotations

import logging
from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

import aiohttp
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import EmbyDataUpdateCoordinator

# Base path of the image proxy view
IMAGE_PROXY_BASE = "/api/embymedia/image"

# How long a signed image URL stays valid. Signed URLs are handed out in entity
# state attributes and browse results, which are refreshed far more often than
# this, and it matches Home Assistant's own expiry for signed media content.
IMAGE_URL_EXPIRY = timedelta(hours=24)

_LOGGER = logging.getLogger(__name__)

# Cache time in seconds when image tag is provided (1 year)
CACHE_TIME_WITH_TAG = 31536000

# Cache time in seconds when no tag is provided (5 minutes)
CACHE_TIME_WITHOUT_TAG = 300

# Chunk size for streaming images (64KB)
STREAM_CHUNK_SIZE = 65536

# Timeout for image fetch requests (seconds)
IMAGE_FETCH_TIMEOUT = 10


def async_get_image_proxy_url(
    hass: HomeAssistant,
    server_id: str,
    item_id: str,
    image_type: str = "Primary",
    max_width: int | None = None,
    max_height: int | None = None,
    tag: str | None = None,
) -> str:
    """Build a signed proxy URL for an Emby image.

    Unlike `EmbyClient.get_image_url`, the returned URL carries no API key -
    the proxy view adds it server-side. Use this anywhere a URL is handed to
    clients, in particular entity state attributes, which are stored in the
    recorder database and served over the REST and WebSocket APIs.

    The URL is signed so the proxy can require authentication while still
    being usable from an `<img>` tag, which cannot send an auth header. The
    signature covers the path and the query parameters, so neither the item
    nor the requested size can be altered after signing.

    Args:
        hass: Home Assistant instance, used to sign the path.
        server_id: The Emby server ID.
        item_id: The item ID.
        image_type: Image type (Primary, Backdrop, Thumb, etc.).
        max_width: Optional maximum width.
        max_height: Optional maximum height.
        tag: Optional image tag for cache busting.

    Returns:
        Signed proxy URL path for the image.
    """
    path = (
        f"{IMAGE_PROXY_BASE}/{quote(server_id, safe='')}"
        f"/{quote(item_id, safe='')}/{quote(image_type, safe='')}"
    )

    params: dict[str, str] = {}
    if max_width is not None:
        params["maxWidth"] = str(max_width)
    if max_height is not None:
        params["maxHeight"] = str(max_height)
    if tag is not None:
        params["tag"] = tag

    if params:
        path = f"{path}?{urlencode(params)}"

    # Signed with the content user: these URLs are built outside any request,
    # during a coordinator refresh or while rendering a browse response.
    try:
        return async_sign_path(hass, path, IMAGE_URL_EXPIRY, use_content_user=True)
    except KeyError:
        # The http integration is a dependency, so its signing support is set
        # up before this runs. Should that ever not hold, hand back the
        # unsigned path: the proxy rejects it, which shows up as a missing
        # image rather than an unauthenticated one.
        _LOGGER.warning("Cannot sign Emby image URL: signed path support unavailable")
        return path


async def async_setup_image_proxy(hass: HomeAssistant) -> None:
    """Set up the Emby image proxy view.

    Args:
        hass: Home Assistant instance.
    """
    hass.http.register_view(EmbyImageProxyView())
    _LOGGER.debug("Emby image proxy view registered")


class EmbyImageProxyView(HomeAssistantView):
    """Proxy view for Emby images.

    This view proxies image requests to the Emby server, handling Emby
    authentication internally so that images can be accessed without exposing
    the API key to clients. Access to the view itself requires a Home
    Assistant signed URL.

    URL pattern: /api/embymedia/image/{server_id}/{item_id}/{image_type}

    Query parameters are forwarded to the Emby server:
    - maxWidth: Maximum image width
    - maxHeight: Maximum image height
    - quality: JPEG quality (0-100)
    - tag: Image tag for cache busting
    """

    url = "/api/embymedia/image/{server_id}/{item_id}/{image_type}"
    name = "api:embymedia:image"
    # Requests must be authenticated. Callers cannot set an auth header on an
    # <img> tag, so URLs are handed out signed by async_get_image_proxy_url and
    # Home Assistant's auth middleware accepts the signature in their place.
    requires_auth = True

    async def get(
        self,
        request: web.Request,
        server_id: str,
        item_id: str,
        image_type: str,
    ) -> web.StreamResponse:
        """Handle GET request for an image with streaming response.

        Uses streaming to avoid loading large images fully into memory.
        Chunks are forwarded from Emby to the client as they arrive.

        Args:
            request: The aiohttp request.
            server_id: The Emby server ID.
            item_id: The item ID to get the image for.
            image_type: The image type (Primary, Backdrop, Thumb, etc.).

        Returns:
            A streaming response with the image data.
        """
        # Get hass from self (set by HA view registration) or from request app
        hass: HomeAssistant = getattr(self, "hass", None) or request.app["hass"]

        # Find the coordinator for the server
        coordinator = self._find_coordinator(hass, server_id)
        if coordinator is None:
            return web.Response(
                status=HTTPStatus.NOT_FOUND,
                text=f"Server {server_id} not found",
            )

        # Build the Emby image URL
        emby_url = self._build_emby_url(
            coordinator.client.base_url,
            coordinator.client.api_key,
            item_id,
            image_type,
            dict(request.query),
        )

        # Fetch the image from Emby with streaming
        session = async_get_clientsession(hass)
        timeout = aiohttp.ClientTimeout(total=IMAGE_FETCH_TIMEOUT)
        try:
            async with session.get(emby_url, timeout=timeout) as response:
                # For error responses, return a regular response with the status
                if response.status != HTTPStatus.OK:
                    body = await response.read()
                    return web.Response(
                        status=response.status,
                        body=body,
                        headers=self._build_response_headers(
                            response.headers.get("Content-Type", "application/octet-stream"),
                            "tag" in request.query,
                        ),
                    )

                # Build streaming response with headers
                headers = self._build_response_headers(
                    response.headers.get("Content-Type", "application/octet-stream"),
                    "tag" in request.query,
                )
                stream_response = web.StreamResponse(
                    status=HTTPStatus.OK,
                    headers=headers,
                )

                # Prepare the response (starts sending headers to client)
                await stream_response.prepare(request)

                # Stream chunks from Emby to client
                async for chunk in response.content.iter_chunked(STREAM_CHUNK_SIZE):
                    await stream_response.write(chunk)

                # Finalize the response
                await stream_response.write_eof()
                return stream_response

        except aiohttp.ClientError as err:
            _LOGGER.warning("Network error fetching image from Emby: %s", err)
            return web.Response(
                status=HTTPStatus.BAD_GATEWAY,
                text="Network error fetching image from Emby server",
            )
        except TimeoutError:
            _LOGGER.warning("Timeout fetching image from Emby")
            return web.Response(
                status=HTTPStatus.GATEWAY_TIMEOUT,
                text="Timeout fetching image from Emby server",
            )
        except OSError as err:
            _LOGGER.warning("OS error fetching image from Emby: %s", err)
            return web.Response(
                status=HTTPStatus.BAD_GATEWAY,
                text="Error fetching image from Emby server",
            )

    def _find_coordinator(
        self,
        hass: HomeAssistant,
        server_id: str,
    ) -> EmbyDataUpdateCoordinator | None:
        """Find the coordinator for a server ID.

        Args:
            hass: Home Assistant instance.
            server_id: The server ID to find.

        Returns:
            The coordinator if found, None otherwise.
        """
        for entry in hass.config_entries.async_entries(DOMAIN):
            if hasattr(entry, "runtime_data") and entry.runtime_data is not None:
                coordinator: EmbyDataUpdateCoordinator = entry.runtime_data.session_coordinator
                if hasattr(coordinator, "server_id") and coordinator.server_id == server_id:
                    return coordinator
                # Also check by unique_id which should match server_id
                if entry.unique_id == server_id:
                    return coordinator
        return None

    def _build_emby_url(
        self,
        base_url: str,
        api_key: str,
        item_id: str,
        image_type: str,
        query_params: dict[str, str],
    ) -> str:
        """Build the full URL to fetch the image from Emby.

        Args:
            base_url: The Emby server base URL.
            api_key: The API key for authentication.
            item_id: The item ID.
            image_type: The image type.
            query_params: Additional query parameters from the request.

        Returns:
            The full URL to fetch the image.
        """
        # Path segments and query values are percent-encoded: this view is
        # unauthenticated, so its inputs are untrusted and must not be able to
        # escape the path or inject extra query parameters into the request
        # that carries the API key.
        url = f"{base_url}/Items/{quote(item_id, safe='')}/Images/{quote(image_type, safe='')}"
        params: dict[str, str] = {"api_key": api_key}

        # Forward relevant query parameters
        for key in ("maxWidth", "maxHeight", "quality", "tag"):
            if key in query_params:
                params[key] = query_params[key]

        return f"{url}?{urlencode(params)}"

    def _build_response_headers(
        self,
        content_type: str,
        has_tag: bool,
    ) -> dict[str, str]:
        """Build response headers with caching information.

        Args:
            content_type: The Content-Type of the image.
            has_tag: Whether an image tag was provided.

        Returns:
            Dictionary of response headers.
        """
        cache_time = CACHE_TIME_WITH_TAG if has_tag else CACHE_TIME_WITHOUT_TAG
        return {
            "Content-Type": content_type,
            "Cache-Control": f"public, max-age={cache_time}",
        }
