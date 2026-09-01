"""Tests for authentication on the Emby image proxy.

The proxy fetches images from Emby using the configured API key, so serving
it to anyone who can reach Home Assistant hands out library artwork - and
any item id can be guessed or enumerated. The view therefore requires
authentication.

An `<img>` tag cannot send an Authorization header, so the URLs handed out in
state attributes and browse results are signed with Home Assistant's own
signed-path support, which its auth middleware accepts in place of a header.

These tests use real signing, so they override the conftest stub.
"""

from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from homeassistant.setup import async_setup_component

from custom_components.embymedia.image_proxy import (
    IMAGE_URL_EXPIRY,
    EmbyImageProxyView,
    async_get_image_proxy_url,
    async_setup_image_proxy,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def stub_image_url_signing() -> Generator[None]:
    """Override the conftest stub: these tests want the real signing."""
    yield


@pytest.fixture
async def hass_with_http(hass: HomeAssistant) -> HomeAssistant:
    """Home Assistant with signed path support available."""
    await async_setup_component(hass, "http", {})
    await hass.async_block_till_done()
    return hass


class TestViewRequiresAuthentication:
    """The proxy view is not open to unauthenticated callers."""

    def test_view_requires_auth(self) -> None:
        """The view demands authentication."""
        assert EmbyImageProxyView().requires_auth is True


class TestSignedUrls:
    """URLs handed to clients carry a valid signature."""

    @pytest.mark.asyncio
    async def test_url_is_signed(self, hass_with_http: HomeAssistant) -> None:
        """A generated URL carries an authSig token."""
        url = async_get_image_proxy_url(hass=hass_with_http, server_id="s1", item_id="i1")

        assert url.startswith("/api/embymedia/image/s1/i1/Primary")
        assert "authSig=" in url

    @pytest.mark.asyncio
    async def test_signature_covers_query_parameters(self, hass_with_http: HomeAssistant) -> None:
        """Size and tag parameters are inside the signed payload.

        Home Assistant signs the path plus its query parameters, so a signed
        URL cannot be edited to request a different item or size.
        """
        signed = async_get_image_proxy_url(
            hass=hass_with_http,
            server_id="s1",
            item_id="i1",
            max_width=300,
            max_height=450,
            tag="abc",
        )

        # The same path with a different tag produces a different signature
        other = async_get_image_proxy_url(
            hass=hass_with_http,
            server_id="s1",
            item_id="i1",
            max_width=300,
            max_height=450,
            tag="xyz",
        )

        assert signed.split("authSig=")[1] != other.split("authSig=")[1]

    @pytest.mark.asyncio
    async def test_signed_url_passes_home_assistant_auth(
        self, hass_with_http: HomeAssistant, hass_client_no_auth: object
    ) -> None:
        """An unauthenticated client may fetch a signed URL.

        The request reaches the view - which answers 404 because no Emby
        server is configured in this test - rather than being rejected as
        unauthorized.
        """
        await async_setup_image_proxy(hass_with_http)
        client = await hass_client_no_auth()  # type: ignore[operator]

        url = async_get_image_proxy_url(
            hass=hass_with_http, server_id="unknown-server", item_id="i1"
        )
        response = await client.get(url)

        assert response.status == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_unsigned_url_is_rejected(
        self, hass_with_http: HomeAssistant, hass_client_no_auth: object
    ) -> None:
        """An unauthenticated client cannot fetch without a signature."""
        await async_setup_image_proxy(hass_with_http)
        client = await hass_client_no_auth()  # type: ignore[operator]

        response = await client.get("/api/embymedia/image/unknown-server/i1/Primary")

        assert response.status == HTTPStatus.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_tampered_signature_is_rejected(
        self, hass_with_http: HomeAssistant, hass_client_no_auth: object
    ) -> None:
        """A signature cannot be reused for a different item."""
        await async_setup_image_proxy(hass_with_http)
        client = await hass_client_no_auth()  # type: ignore[operator]

        url = async_get_image_proxy_url(
            hass=hass_with_http, server_id="unknown-server", item_id="i1"
        )
        tampered = url.replace("/i1/", "/i2/")

        response = await client.get(tampered)

        assert response.status == HTTPStatus.UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_url_carries_no_api_key(self, hass_with_http: HomeAssistant) -> None:
        """The Emby API key never appears in a signed URL."""
        url = async_get_image_proxy_url(hass=hass_with_http, server_id="s1", item_id="i1")

        assert "api_key" not in url

    @pytest.mark.asyncio
    async def test_expiry_matches_home_assistant_content_expiry(self) -> None:
        """Signed URLs outlive the refresh that produced them."""
        # Discovery data refreshes at most hourly, so a shorter expiry would
        # leave stale attributes pointing at URLs that no longer work
        assert timedelta(hours=1) <= IMAGE_URL_EXPIRY


class TestSigningUnavailable:
    """Signing failures must not break the entity that needs a URL."""

    def test_unsigned_path_returned_when_signing_unavailable(self) -> None:
        """Without http's signing support the call still returns a path.

        The http integration is a manifest dependency so this should not
        happen; if it ever did, an unsigned path is rejected by the view,
        which shows as a missing image rather than an unauthenticated one.
        """
        hass = MagicMock()
        hass.data = {}  # no signing secret, no content user

        url = async_get_image_proxy_url(hass=hass, server_id="s1", item_id="i1")

        assert url == "/api/embymedia/image/s1/i1/Primary"
        assert "authSig=" not in url
