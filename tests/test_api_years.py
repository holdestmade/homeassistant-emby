"""Tests for how library years are resolved.

Reading the list of years used to mean transferring the entire library: the
last-resort path requests up to 10,000 items with `Fields=ProductionYear`
just to read one integer off each. Emby's `/Items/Filters` endpoint returns
the distinct production years as a small array, deduplicated server-side, so
it is tried before falling back to that scan.

Order of preference:

1. `/Years` - the purpose-built endpoint, 500s on many servers
2. `/Items/Filters` - distinct years, cheap
3. full item scan - last resort
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.embymedia.api import EmbyClient
from custom_components.embymedia.exceptions import EmbyNotFoundError, EmbyServerError


@pytest.fixture
def client() -> EmbyClient:
    """Create a client with a clean browse cache."""
    return EmbyClient(host="emby.local", port=8096, api_key="test-api-key")


class TestYearsPreferTheFiltersEndpoint:
    """The filters endpoint is used before scanning the library."""

    @pytest.mark.asyncio
    async def test_filters_used_when_years_endpoint_fails(self, client: EmbyClient) -> None:
        """A 500 from /Years falls through to /Items/Filters, not a scan."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("500 Internal Server Error"),
                {"Years": [1999, 2020, 2019]},
            ]

            result = await client.async_get_years("user-1", parent_id="lib-1")

            assert [item["Name"] for item in result] == ["2020", "2019", "1999"]

        # Exactly two calls: no library scan happened
        assert mock_request.await_count == 2
        endpoints = [call.args[1] for call in mock_request.await_args_list]
        assert endpoints[0].startswith("/Years")
        assert endpoints[1].startswith("/Items/Filters")

    @pytest.mark.asyncio
    async def test_filters_request_carries_the_query_scope(self, client: EmbyClient) -> None:
        """User, library and item type are passed to the filters endpoint."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("boom"),
                {"Years": [2020]},
            ]

            await client.async_get_years(
                "user-1", parent_id="lib-movies", include_item_types="Movie"
            )

        endpoint = mock_request.await_args_list[1].args[1]
        assert "UserId=user-1" in endpoint
        assert "ParentId=lib-movies" in endpoint
        assert "IncludeItemTypes=Movie" in endpoint

    @pytest.mark.asyncio
    async def test_years_are_deduplicated_and_sorted_newest_first(self, client: EmbyClient) -> None:
        """Duplicate and invalid years are dropped."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("boom"),
                {"Years": [2020, 2020, -1, 0, 1998]},
            ]

            result = await client.async_get_years("user-1")

        assert [item["Name"] for item in result] == ["2020", "1998"]
        assert all(item["Type"] == "Year" for item in result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure", [EmbyServerError("500"), EmbyNotFoundError("404")])
    async def test_scan_is_used_when_filters_unavailable(
        self, client: EmbyClient, failure: Exception
    ) -> None:
        """An older server without /Items/Filters still gets years."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("500"),
                failure,
                {"Items": [{"Id": "m1", "ProductionYear": 2021}]},
            ]

            result = await client.async_get_years("user-1")

        assert [item["Name"] for item in result] == ["2021"]
        assert mock_request.await_count == 3

    @pytest.mark.asyncio
    async def test_malformed_filters_response_falls_back(self, client: EmbyClient) -> None:
        """A response without a usable Years array falls through to the scan."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("500"),
                {"Years": "not-a-list"},
                {"Items": [{"Id": "m1", "ProductionYear": 2005}]},
            ]

            result = await client.async_get_years("user-1")

        assert [item["Name"] for item in result] == ["2005"]


class TestYearScanIsMinimal:
    """The last-resort scan asks for as little as possible."""

    @pytest.mark.asyncio
    async def test_scan_disables_unneeded_work(self, client: EmbyClient) -> None:
        """Images, user data and the total count are all switched off.

        Only ProductionYear is read, so everything else is server work and
        payload for nothing.
        """
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("500"),
                {"Years": []},
                {"Items": []},
            ]

            await client.async_get_years("user-1")

        endpoint = mock_request.await_args_list[2].args[1]
        assert "Fields=ProductionYear" in endpoint
        assert "EnableImages=false" in endpoint
        assert "EnableUserData=false" in endpoint
        assert "EnableTotalRecordCount=false" in endpoint


class TestYearsCaching:
    """Results are cached regardless of which source produced them."""

    @pytest.mark.asyncio
    async def test_filters_result_is_cached(self, client: EmbyClient) -> None:
        """A second call for the same scope makes no further requests."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                EmbyServerError("500"),
                {"Years": [2020]},
            ]

            first = await client.async_get_years("user-1", parent_id="lib-1")
            second = await client.async_get_years("user-1", parent_id="lib-1")

        assert first == second
        assert mock_request.await_count == 2
