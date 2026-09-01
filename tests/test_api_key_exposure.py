"""Regression tests: the Emby API key must never reach clients.

`EmbyClient.get_image_url` embeds the API key as a query parameter. Any URL
built that way must stay server-side. Entity state attributes are the worst
place for one to leak into: they are

* stored in the recorder database, for the life of that history
* returned by `GET /api/states` to any holder of a Home Assistant token,
  including read-only users
* visible in Developer Tools and included in diagnostics

Discovery sensors published `image_url` and `backdrop_url` attributes built
with `get_image_url`, leaking the key. They now use the image proxy view,
which adds the key server-side.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from custom_components.embymedia.coordinator_discovery import (
    EmbyDiscoveryData,
    EmbyUserCounts,
)
from custom_components.embymedia.sensor_discovery import (
    EmbyContinueWatchingSensor,
    EmbyNextUpSensor,
    EmbyRecentlyAddedSensor,
    EmbySuggestionsSensor,
)

if TYPE_CHECKING:
    pass

API_KEY = "SUPER-SECRET-API-KEY"


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Discovery coordinator whose client uses a recognisable API key."""
    from custom_components.embymedia.api import EmbyClient

    coordinator = MagicMock()
    coordinator.server_id = "server123"
    coordinator.server_name = "Emby Server"
    coordinator.user_id = "user456"
    coordinator.user_name = "testuser"
    coordinator.last_update_success = True
    # A real client, so get_image_url behaves exactly as in production
    coordinator.client = EmbyClient(host="emby.local", port=8096, api_key=API_KEY, ssl=True)

    item = {
        "Id": "item1",
        "Name": "Test Item",
        "Type": "Episode",
        "SeriesId": "series1",
        "SeriesName": "Test Series",
        "SeriesPrimaryImageTag": "seriestag",
        "ImageTags": {"Primary": "tag1", "Backdrop": "tag2"},
        "UserData": {"PlaybackPositionTicks": 0, "PlayedPercentage": 0},
    }
    coordinator.data = EmbyDiscoveryData(
        next_up=[item],
        continue_watching=[item],
        recently_added=[item],
        suggestions=[item],
        user_counts=EmbyUserCounts(
            favorites_count=0,
            played_count=0,
            resumable_count=0,
            playlist_count=0,
        ),
    )
    return coordinator


SENSOR_CLASSES = [
    EmbyNextUpSensor,
    EmbyContinueWatchingSensor,
    EmbyRecentlyAddedSensor,
    EmbySuggestionsSensor,
]


class TestApiKeyNotInStateAttributes:
    """No discovery sensor may publish the API key."""

    @pytest.mark.parametrize("sensor_class", SENSOR_CLASSES)
    def test_api_key_absent_from_attributes(
        self,
        mock_coordinator: MagicMock,
        sensor_class: type,
    ) -> None:
        """The rendered attributes must not contain the API key."""
        sensor = sensor_class(mock_coordinator, "Emby Server")

        rendered = repr(sensor.extra_state_attributes)

        assert API_KEY not in rendered
        assert "api_key" not in rendered

    @pytest.mark.parametrize("sensor_class", SENSOR_CLASSES)
    def test_image_urls_use_the_proxy(
        self,
        mock_coordinator: MagicMock,
        sensor_class: type,
    ) -> None:
        """Image URLs point at the proxy view, which holds the key."""
        sensor = sensor_class(mock_coordinator, "Emby Server")

        attributes = sensor.extra_state_attributes
        assert attributes is not None

        for item in attributes["items"]:
            for key in ("image_url", "backdrop_url"):
                url = item.get(key)
                if url is not None:
                    assert url.startswith("/api/embymedia/image/")


class TestImageProxyUrlBuilder:
    """Test the proxy URL builder used in place of direct Emby URLs."""

    def test_builds_path_with_encoded_segments(self) -> None:
        """Path segments are percent-encoded."""
        from custom_components.embymedia.image_proxy import async_get_image_proxy_url

        url = async_get_image_proxy_url(
            server_id="server 123",
            item_id="item/../secret",
            image_type="Primary",
        )

        assert url == "/api/embymedia/image/server%20123/item%2F..%2Fsecret/Primary"

    def test_includes_optional_parameters(self) -> None:
        """Size and tag parameters are added when provided."""
        from custom_components.embymedia.image_proxy import async_get_image_proxy_url

        url = async_get_image_proxy_url(
            server_id="s1",
            item_id="i1",
            max_width=300,
            max_height=450,
            tag="abc",
        )

        assert url.startswith("/api/embymedia/image/s1/i1/Primary?")
        assert "maxWidth=300" in url
        assert "maxHeight=450" in url
        assert "tag=abc" in url

    def test_carries_no_api_key(self) -> None:
        """The proxy URL never carries credentials."""
        from custom_components.embymedia.image_proxy import async_get_image_proxy_url

        url = async_get_image_proxy_url(server_id="s1", item_id="i1", tag="t")

        assert "api_key" not in url


class TestProxyUpstreamUrlIsEncoded:
    """The unauthenticated proxy must not let inputs alter the upstream URL."""

    def test_query_values_cannot_inject_parameters(self) -> None:
        """A crafted tag cannot append extra query parameters."""
        from custom_components.embymedia.image_proxy import EmbyImageProxyView

        view = EmbyImageProxyView()

        url = view._build_emby_url(
            "https://emby.local:8096",
            "secret-key",
            "item1",
            "Primary",
            {"tag": "abc&Format=raw"},
        )

        # The ampersand is encoded, so Format is part of the tag value
        assert "&Format=raw" not in url
        assert "Format%3Draw" in url or "Format%3draw" in url

    def test_path_segments_cannot_escape(self) -> None:
        """A crafted item id cannot traverse to another Emby endpoint."""
        from custom_components.embymedia.image_proxy import EmbyImageProxyView

        view = EmbyImageProxyView()

        url = view._build_emby_url(
            "https://emby.local:8096",
            "secret-key",
            "../../System/Info",
            "Primary",
            {},
        )

        assert "/Items/..%2F..%2FSystem%2FInfo/Images/Primary" in url
