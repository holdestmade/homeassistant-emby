# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.3] - 2026-09-01

### Fixed
- **Home Assistant startup blocked for 10+ minutes** (troykelly#323, troykelly#331)
  - The WebSocket receive loop and the health check loop were created with
    `hass.async_create_task`. Bootstrap waits for every tracked task, so these
    never-ending loops held startup open until the bootstrap timeout, and
    disabling the integration was the only workaround
  - Both are now created with `hass.async_create_background_task`, which is
    excluded from the startup wait and still cancelled on shutdown
- **Image proxy served anyone who could reach Home Assistant**
  - The proxy fetches artwork using the Emby API key but declared
    `requires_auth = False`, so any unauthenticated caller who could reach
    Home Assistant could pull artwork for any item id
  - It now requires authentication. URLs are handed out signed with Home
    Assistant's signed-path support, which an `<img>` tag can load without an
    auth header, and whose signature covers the item, image type and size
  - Note: URLs are signed at generation time and regenerate on each refresh.
    Hand-written dashboard references to `/api/embymedia/image/...` will need
    to use the entity attribute instead of a hard-coded URL
- **Emby API key exposed in state attributes**
  - Discovery sensors published `image_url` and `backdrop_url` built with an
    `api_key` query parameter. State attributes are stored in the recorder
    database and returned by `GET /api/states` to any token holder, so the key
    was exposed to every Home Assistant user and persisted in history
  - These URLs now go through the integration's image proxy, which adds the
    key server-side. Media player artwork was never affected
  - Hardened the (unauthenticated) image proxy: item id, image type and
    forwarded query values are percent-encoded, so a crafted request cannot
    inject query parameters into, or redirect, the authenticated upstream call
- **Entity IDs repeated the device name**
  - `EmbyEntity` and the server buttons overrode `suggested_object_id`, which
    Home Assistant treats as an `object_id_base` and prefixes with the device
    name, producing IDs like `media_player.living_room_living_room` and
    `button.server_emby_server_refresh_library`
  - Home Assistant now derives the IDs; the optional 'Emby' prefix continues to
    work through the device name. Existing entities keep their registered IDs
- **Background tasks outlived the config entry**
  - The health check loop was never cancelled on unload, so each reload left
    another loop polling the server through a stale client
  - Added `EmbyDataUpdateCoordinator.async_shutdown`, registered as the entry's
    unload callback, which stops the health check loop and the WebSocket
- **WebSocket never reconnected after a dropped connection**
  - A dropped connection fell back to polling permanently; the recovery path
    reconnected without re-subscribing or restarting the receive loop, and
    awaited a backoff of up to five minutes inside the coordinator update path
  - Reconnection now runs as a background task that re-subscribes and restarts
    the receive loop
- **Request timeout was silently ignored**
  - The client's 10 second timeout only applied when it created its own
    session. Home Assistant always injects a shared session, so aiohttp's
    5 minute default applied to every request
  - The timeout is now passed per request; the WebSocket handshake is bounded too
- **Setup failed permanently on a transient server error**
  - An Emby server still starting up returns 5xx, which raised `EmbyServerError`
    out of setup and left the entry in a permanent error state
  - Transient errors now raise `ConfigEntryNotReady` so Home Assistant retries
- **Two options shown as raw keys in the UI**
  - `library_scan_interval` and `server_scan_interval` were labelled in
    `strings.json` but missing from `translations/en.json`, which is the file
    Home Assistant serves, so the options dialog displayed the bare option
    names. English is every locale's fallback, so all languages were affected
  - Also removed translation entries for the retired per-platform prefix
    options, which no longer correspond to anything in the config flow
- **Deprecated `via_device` device registry parameter**
  - Entities linked to the server device with `via_device`, deprecated in
    favour of `via_device_id` and removed in Home Assistant 2027.8
  - The integration now emits whichever key the running Home Assistant
    supports, so it keeps working on 2025.11.3 as well as current releases
- **Coalesced requests could deadlock**
  - If the first caller of a coalesced request was cancelled, its shared future
    was never resolved and every other waiter hung forever
  - The shared request now runs in its own shielded task
- **WebSocket refresh debounce used a wall clock**
  - A backwards clock step (DST fall-back, NTP correction) made the elapsed
    time negative and blocked WebSocket-driven refreshes for up to an hour;
    it now measures elapsed time on the monotonic clock
- **Browse cache evicted entries unnecessarily**
  - `set()` evicted whenever the cache was full, including when overwriting an
    existing key, so refreshing a hot entry dropped an unrelated one

### Changed
- **Repository now ships the integration only** - the test suite, CI
  workflows, development container and contributor tooling were removed.
  Documentation links and the HACS install instructions point at this fork
  rather than the upstream project
- **Device name prefix is now a single option** (config entry version 2)
  - `prefix_media_player`, `prefix_notify` and `prefix_remote` all applied to
    the same device - one device backs every entity for a client - so only
    whichever platform registered last took effect. `prefix_button` applied to
    the shared server device, whose name the integration never sets, so it did
    nothing at all
  - All four are replaced by `prefix_device_names`. Existing entries migrate
    automatically, carrying over the `prefix_media_player` value
- Browse and media source thumbnails now go through the image proxy, so no
  Emby API key reaches the browser with a browse response
- Coordinator first refreshes now run concurrently during setup instead of
  serially, which was one round of API calls per Emby user
- POST and DELETE now report HTTP status the same way GET does: a 404 raises
  `EmbyNotFoundError` and a 5xx raises `EmbyServerError`, where both
  previously surfaced as `EmbyConnectionError`

### Technical
- Library years are now read from Emby's `/Items/Filters` endpoint, which
  returns the distinct production years as a small array. The previous
  fallback transferred up to 10,000 items to read one field off each; it
  remains as a last resort for servers without the endpoint, and now asks the
  server to skip image metadata, per-user data and the total-count query
- `api.py`: the four near-identical request methods are now thin wrappers over
  a single `_send`, removing ~150 lines of duplicated status handling, error
  translation and metrics code. All 74 call sites are unchanged

- All of the above was developed against the project's test suite (1963
  tests passing at the time of the change); the suite, CI workflows and
  development tooling have since been removed from this repository, which
  now ships the integration and its documentation only


## [0.6.0] - 2026-01-11

### Fixed
- **Reinstallation Fails with Duplicate unique_id** (#312)
  - Added final duplicate check in config flow before entry creation to prevent race conditions (#314)
  - Config flow now aborts with `already_configured` if entry with same unique_id is created between steps
  - Verified Home Assistant framework properly handles orphaned entries via SETUP_RETRY state (#316)
  - Setup cancellation now handled gracefully by HA framework (#315)

### Added
- **Comprehensive Reinstallation Tests** (#317)
  - Full install-unload-remove-reinstall cycle tests
  - Concurrent configuration attempt handling
  - Partial unload recovery scenarios
  - Multiple server reinstallation tests
  - Edge case tests for rapid install/uninstall cycles

### Technical
- 1888 tests with 100% code coverage
- Improved config flow robustness for HA 2026.3+ compatibility

## [0.5.1] - 2026-01-10

### Fixed
- **Device Triggers Not Firing** (#285)
  - Fixed device triggers (playback_started, playback_stopped, etc.) not firing when session updates came through the polling path
  - Events now fire reliably from both polling and WebSocket paths
  - Added edge case handling: fire playback_started for new sessions that are already playing

### Technical
- 1864 tests with 100% code coverage
- Fixed HA 2025 test compatibility for options flow
- Fixed type inference in coordinator_sensors.py

## [0.5.0] - 2026-01-10

### Added
- **Efficiency Optimizations** (#287-#296)
  - WebSocket-aware polling: Disable polling when WebSocket is stable, resume on disconnect (#287)
  - Discovery data caching with 30-minute TTL and WebSocket invalidation (#288)
  - Extended library polling interval (10x) when WebSocket is active (#289)
  - Request coalescing for concurrent identical API requests (#290)
  - Batch user API calls: consolidate per-user counts into single request (#291)
  - Configurable polling intervals via options flow (#292)
  - API call metrics in diagnostics (#293)
  - `always_update=False` on all DataUpdateCoordinators (#295)
  - `PARALLEL_UPDATES` on all entity platforms (#296)

### Documentation
- Added ARCHITECTURE.md with system design overview (#294)
- Added EFFICIENCY.md documenting optimization strategies (#294)

### Technical
- 1863 tests with 100% code coverage

## [0.4.1] - 2025-11-30

### Added
- **Playing Sessions Sensor** (#276)
  - New sensor: `sensor.{server}_playing_sessions` - Count of currently playing sessions
  - Proper translations for sensor name and state attributes

### Fixed
- **Artist Count Accuracy** (#277)
  - Artist count sensor now uses dedicated `async_get_artist_count` API for accurate counts
  - Added workaround for BoxSet (collections) count always returning zero from Emby API

### Changed
- Migrated to GitHub Issues/Projects workflow for project management (#278)
- Added GitHub issue templates with AI-powered triage support (#275)

## [0.4.0] - 2025-11-29

### Added
- **Enhanced WebSocket Events** (Phase 21)
  - New event: `embymedia_library_updated` - Fires when items are added/updated/removed from libraries
  - New event: `embymedia_user_data_changed` - Fires when favorites, played status, or ratings change
  - New event: `embymedia_notification` - Forwards Emby server notifications to Home Assistant
  - New event: `embymedia_user_changed` - Fires when user accounts are updated or deleted
  - TypedDicts: `EmbyLibraryChangedData`, `EmbyUserDataChangedData`, `EmbyNotificationData`, `EmbyUserChangedData`
  - Automatic browse cache invalidation on library changes
  - Debounced library coordinator refresh (5-second delay) on library changes
  - Documentation with example automations in docs/AUTOMATIONS.md

- **Server Administration** (Phase 20)
  - New service: `embymedia.run_scheduled_task` - Trigger any scheduled task on demand
  - New service: `embymedia.restart_server` - Restart the Emby server (requires admin)
  - New service: `embymedia.shutdown_server` - Shutdown the Emby server (requires admin)
  - New sensor: `sensor.{server}_plugins` - Plugin count with full plugin list in attributes
  - New button: `button.{server}_run_library_scan` - Quick trigger library scan
  - API methods: `async_run_scheduled_task`, `async_restart_server`, `async_shutdown_server`, `async_get_plugins`

- **Collection Management** (Phase 19)
  - New service: `embymedia.create_collection` - Create new collections (BoxSets)
  - New service: `embymedia.add_to_collection` - Add items to existing collections
  - New service: `embymedia.remove_from_collection` - Remove items from collections
  - New sensor: `sensor.{server}_collections` - Shows collection count (requires user_id configuration)
  - API methods: `async_create_collection`, `async_add_to_collection`, `async_remove_from_collection`, `async_get_collections`
  - TypedDicts for collection API type safety

- **Person Browsing** (Phase 19)
  - Browse actors, directors, writers in movie libraries
  - View person filmography - see all movies/shows featuring a person
  - Person images displayed when available
  - API methods: `async_get_persons`, `async_get_person_items`

- **Tag Browsing** (Phase 19)
  - Browse user-defined tags in movie libraries
  - Filter movies by tag to view tagged content
  - API methods: `async_get_tags`, `async_get_items_by_tag`
  - Cached tag lists for improved performance

- **Enhanced Movie Library Categories**
  - "People" category added to movie library browser
  - "Tags" category added to movie library browser

- **User Activity & Statistics** (Phase 18)
  - New sensor: `sensor.{server}_last_activity` - Most recent server activity with details
  - New sensor: `sensor.{server}_connected_devices` - Count of registered devices with device list
  - Activity log API: `async_get_activity_log` - Fetch server activity entries
  - Device management API: `async_get_devices` - List all registered devices
  - TypedDicts for activity and device API type safety

- **Playlist Management** (Phase 17)
  - New service: `embymedia.create_playlist` - Create new Audio or Video playlists
  - New service: `embymedia.add_to_playlist` - Add items to existing playlists
  - New service: `embymedia.remove_from_playlist` - Remove items from playlists using PlaylistItemId
  - New sensor: `sensor.{server}_playlists` - Shows playlist count (requires user_id configuration)
  - TypedDicts for playlist API type safety

- **Code Quality & Performance Optimization** (Phase 22)
  - Parallel API calls for coordinator data fetching (discovery, server, library)
  - Streaming image proxy for efficient memory usage
  - Playback session memory cleanup to prevent memory leaks
  - BLAKE2b hash algorithm replacing MD5 for cache keys
  - Parallel service execution for non-dependent operations
  - Optimized web player detection with O(1) lookup
  - Configurable WebSocket session interval option
  - Enhanced error handling with specific exception types

- **Enhanced Playback** (Phase 14)
  - New service: `embymedia.clear_queue` - Clear playback queue
  - New attribute: `similar_items` - List of similar content on media players
  - Queue attributes: `queue_items`, `queue_position`, `queue_total`

### Changed
- Replaced MD5 with BLAKE2b for cache key hashing (improved security)
- Replaced broad exception handling with specific exception types
- Extracted letter browsing helper for code reuse
- Image proxy now uses streaming for better memory efficiency

### Technical
- 1649 tests with 100% code coverage
- Internationalization: 9 language translations added

## [0.3.0] - 2025-11-27

### Added
- **Dynamic Transcoding for Universal Media Playback** (Phase 13)
  - Universal audio endpoint for maximum device compatibility
  - Predefined device profiles for different playback scenarios
  - Transcoding session management with proper lifecycle handling
  - PlaybackInfo API methods for querying playback capabilities and stream URLs
  - Device ID generation functions for transcoding sessions

### Fixed
- **Audio-only Device Compatibility**: Media browsing now uses MIME type prefixes (`audio/`, `video/`) instead of MediaType constants, allowing audio-only Cast devices (Sonos, etc.) to see and play music content
- **Audio Playback**: Fixed empty UserId in universal audio endpoint causing playback failures

### Technical
- Added `homeassistant-stubs` to test dependencies for consistent mypy behavior between local development and CI
- 1102 tests with 100% code coverage

## [0.2.2] - 2025-11-27

### Fixed
- **Artist Browsing**: Clicking on an artist in the media browser now correctly shows their albums instead of attempting playback
  - Added `musicartist` and `musicalbum` to expandable types
  - Added artist content type handler to fetch albums via `async_get_artist_albums` API

## [0.2.1] - 2025-11-27

### Added
- **Studio/Network Browsing** - Browse movies and TV shows by studio or network
  - Movies > Studio shows list of production studios
  - TV Shows > Studio shows list of networks/studios
- **Enhanced Music Library Browsing** - Full category navigation for music libraries
  - Artists A-Z letter navigation
  - Albums A-Z letter navigation
  - Genre browsing with albums
  - Playlist browsing

### Fixed
- Fixed "Unknown error" when browsing movies by year in media source
- Fixed "Unknown error" when browsing TV shows by year in media source
- Fixed year browsing when Emby `/Years` endpoint fails (automatic fallback to extracting years from items)
- Improved error handling in media source browsing with descriptive messages
- Synchronized media source browsing features with media player entity browsing

## [0.2.0] - 2025-11-26

### Added
- **Sensor Platform** (Phase 12)
  - Binary sensors for server status:
    - `binary_sensor.{server}_connected` - Server connectivity
    - `binary_sensor.{server}_pending_restart` - Restart required indicator
    - `binary_sensor.{server}_update_available` - Update availability
    - `binary_sensor.{server}_library_scan_active` - Library scan status with progress attribute
  - Numeric sensors for server statistics:
    - `sensor.{server}_server_version` - Server version (diagnostic)
    - `sensor.{server}_running_tasks` - Active scheduled tasks count
    - `sensor.{server}_active_sessions` - Connected client count
  - Library count sensors (1-hour polling):
    - `sensor.{server}_movies` - Total movie count
    - `sensor.{server}_tv_shows` - Total TV series count
    - `sensor.{server}_episodes` - Total episode count
    - `sensor.{server}_songs` - Total song count
    - `sensor.{server}_albums` - Total album count
    - `sensor.{server}_artists` - Total artist count
  - New coordinators for sensor data:
    - `EmbyServerCoordinator` - Server info polling (5-minute interval)
    - `EmbyLibraryCoordinator` - Library counts polling (1-hour interval)
  - `EmbyRuntimeData` class to manage multiple coordinators

### Technical
- 941 tests with 100% code coverage
- TypedDict definitions for sensor API responses
- Backward-compatible runtime_data structure

### Fixed
- Release workflow permissions for uploading zip artifacts

## [0.1.0] - 2025-11-26

### Added
- Initial release of Home Assistant Emby Media integration
- Media player entities for Emby clients with full playback control
- Real-time state updates via WebSocket connection
- Media browsing support for all Emby library types:
  - Movies (A-Z, year, decade, genre, collections)
  - TV Shows (A-Z, year, decade, genre, seasons, episodes)
  - Music (artists, albums, genres, playlists)
  - Live TV channels
  - Playlists and collections
- Media source provider for cross-player playback
- Voice assistant search support (`async_search_media`)
- Image proxy for authenticated media artwork
- Config flow with connection validation
- Options flow for customizable settings:
  - Scan interval (5-300 seconds)
  - WebSocket enable/disable
  - Device filtering
  - Transcoding options (direct play, container, bitrate)
  - Entity name prefix toggles ("Emby" prefix per entity type)
- Multiple users support with per-user libraries
- Custom services:
  - `embymedia.send_message` - Display notifications on clients
  - `embymedia.send_command` - Send navigation commands
  - `embymedia.mark_played` / `embymedia.mark_unplayed` - Manage watch status
  - `embymedia.add_favorite` / `embymedia.remove_favorite` - Manage favorites
  - `embymedia.refresh_library` - Trigger library scan
- Device triggers for automation:
  - Playback started/stopped/paused/resumed
  - Session connected/disconnected
  - Media changed
- Diagnostics download for troubleshooting
- Remote entity for navigation commands
- Notify entity for on-screen messages
- Button entity for server actions

### Technical
- Python 3.13+ support (Home Assistant 2025.x)
- 100% test coverage with 815+ tests
- Strict type checking with mypy
- TypedDict definitions for all API responses
- WebSocket with exponential backoff reconnection
- Browse cache with LRU + TTL for performance
- Graceful degradation on partial failures

[0.7.3]: https://github.com/holdestmade/homeassistant-emby/compare/v0.6.0...v0.7.3
[0.6.0]: https://github.com/troykelly/homeassistant-emby/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/troykelly/homeassistant-emby/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/troykelly/homeassistant-emby/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/troykelly/homeassistant-emby/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/troykelly/homeassistant-emby/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/troykelly/homeassistant-emby/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/troykelly/homeassistant-emby/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/troykelly/homeassistant-emby/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/troykelly/homeassistant-emby/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/troykelly/homeassistant-emby/releases/tag/v0.1.0
