<p align="center">
  <img src="https://emby.media/resources/logowhite_1881.png" alt="Emby Logo" width="180">
</p>

<h1 align="center">Emby Media for Home Assistant</h1>

<p align="center">
  <strong>Your media server. Your smart home. Seamlessly connected.</strong>
</p>

---

<h2 align="center"> Quick Start</h2>

<table align="center">
<tr>
<td width="33%" align="center">

**Install**

Open HACS → Custom repositories
Add: `troykelly/homeassistant-emby`
Download **Emby Media**

</td>
<td width="33%" align="center">

**Configure**

Settings → Devices & Services
Add Integration → **Emby Media**
Enter host + API key

</td>
<td width="33%" align="center">

**Enjoy**

Your Emby clients appear
as media players instantly!

</td>
</tr>
</table>

<p align="center">
  <a href="#-installation"><strong> Detailed Install Guide</strong></a> ·
  <a href="#getting-an-api-key"><strong> Get API Key</strong></a> ·
  <a href="docs/TROUBLESHOOTING.md"><strong> Having Issues?</strong></a>
</p>

---

<h3 align="center"> Jump to what you need</h3>

<p align="center">
  <a href="#-what-can-you-do-with-it"> Features</a> ·
  <a href="#-installation"> Installation</a> ·
  <a href="#-automate-your-media"> Automations</a> ·
  <a href="#-server-monitoring"> Sensors</a> ·
  <a href="#-all-the-services"> Services</a> ·
  <a href="#-troubleshooting"> Troubleshooting</a> ·
  <a href="#-for-developers"> Developers</a>
</p>

---

##  What Can You Do With It?

<table>
<tr>
<td width="50%">

###  Control Any Emby Client

Every device running Emby becomes controllable from Home Assistant. Play, pause, skip, seek, adjust volume—all from your dashboard, automations, or voice.

**Works with:** TVs, Roku, Fire TV, Apple TV, phones, tablets, web browsers, and more.

</td>
<td width="50%">

###  Smart Home + Media = Magic

Lights dim when your movie starts. Playback pauses when the doorbell rings. Volume drops at night. Your media experience adapts to your life.

**[See automation examples →](#-automate-your-media)**

</td>
</tr>
<tr>
<td width="50%">

###  "Hey Google, play The Office"

Full voice assistant integration. Search your library, play content by name, control playback—all by voice through Google Home, Alexa, or Home Assistant's Assist.

</td>
<td width="50%">

### 📺 Browse Your Library

Navigate your entire Emby library right from Home Assistant. Browse by genre, year, actor, or collection. Click to play on any connected device.

</td>
</tr>
<tr>
<td width="50%">

### 🔊 Play Emby Music Anywhere

Cast your Emby music library to ANY Home Assistant media player—Sonos, Chromecast, smart speakers. Your music, everywhere.

</td>
<td width="50%">

###  Real-Time Everything

WebSocket connection means instant updates. See what's playing, track progress, react to events—no polling delays, no stale data.

</td>
</tr>
</table>

---

##  Requirements

| Component | Minimum Version |
|-----------|----------------|
| **Home Assistant** | 2026.6.0+ |
| **Emby Server** | 4.9.1.90+ |
| **HACS** | Latest (for easy installation) |

---

##  Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click ⋮ → **Custom repositories**
3. Add `https://github.com/holdestmade/homeassistant-emby` as **Integration**
4. Search for **"Emby Media"** and click **Download**
5. **Restart Home Assistant**

### Option 2: Manual

1. Download the [latest release](https://github.com/holdestmade/homeassistant-emby/releases)
2. Extract `embymedia` folder to `config/custom_components/`
3. **Restart Home Assistant**

<details>
<summary> Expected folder structure</summary>

```
config/
├── configuration.yaml
└── custom_components/
    └── embymedia/
        ├── __init__.py
        ├── manifest.json
        └── ... (other files)
```

</details>

---

##  Configuration

### Getting an API Key

1. Open **Emby Server Dashboard** (`http://your-server:8096`)
2. Go to **Settings** → **Advanced** → **API Keys**
3. Click **+ New API Key** → Name it "Home Assistant" → **OK**
4. Copy the generated key

### Adding the Integration

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search **"Emby Media"**
3. Enter your details:

| Field | Example | Notes |
|-------|---------|-------|
| Host | `192.168.1.100` | IP or hostname |
| Port | `8096` | Default HTTP port |
| Use SSL | ☐ | Check for HTTPS |
| API Key | `abc123...` | From step above |
| Verify SSL | ☐ | Uncheck for self-signed certs |

4. Click **Submit** — entities appear automatically!

**[📖 Full Configuration Reference →](docs/CONFIGURATION.md)**

---

##  Automate Your Media

### Dim Lights for Movie Night

```yaml
automation:
  - alias: "Movie mode lighting"
    trigger:
      - platform: state
        entity_id: media_player.emby_living_room_tv
        to: "playing"
    condition:
      - condition: template
        value_template: "{{ state_attr(trigger.entity_id, 'media_content_type') == 'movie' }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 10
          transition: 3
```

### Pause When Doorbell Rings

```yaml
automation:
  - alias: "Pause for doorbell"
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: media_player.media_pause
        target:
          entity_id: media_player.emby_living_room_tv
      - service: notify.send_message
        target:
          entity_id: notify.emby_living_room_tv
        data:
          message: "Someone's at the door! 🚪"
```

### Nightly Library Refresh

```yaml
automation:
  - alias: "Refresh library at 3am"
    trigger:
      - platform: time
        at: "03:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.emby_server_run_library_scan
```

<p align="center">
  <strong><a href="docs/AUTOMATIONS.md">50+ More Automation Examples →</a></strong>
</p>

---

## 📊 Server Monitoring

Get visibility into your Emby server with built-in sensors:

### Server Health
| Sensor | What it shows |
|--------|---------------|
| `binary_sensor.*_connected` | Is server reachable? |
| `binary_sensor.*_pending_restart` | Restart required? |
| `binary_sensor.*_update_available` | Update available? |
| `binary_sensor.*_library_scan_active` | Scan in progress? (with % progress) |

### Library Statistics
| Sensor | What it shows |
|--------|---------------|
| `sensor.*_movies` | Total movie count |
| `sensor.*_tv_shows` | Total series count |
| `sensor.*_episodes` | Total episode count |
| `sensor.*_songs` | Total song count |
| `sensor.*_albums` | Total album count |
| `sensor.*_artists` | Total artist count |

### Activity
| Sensor | What it shows |
|--------|---------------|
| `sensor.*_active_sessions` | Connected clients |
| `sensor.*_running_tasks` | Background tasks |
| `sensor.*_plugins` | Installed plugins (with list) |
| `sensor.*_last_activity` | Recent server activity |

---

##  Live TV & DVR

Full Live TV support for Emby servers with tuners configured:

| Feature | Description |
|---------|-------------|
| **Browse Channels** | Navigate Live TV channels in media browser |
| **Recording Sensors** | Track recordings, active recordings, scheduled timers |
| **Schedule Recordings** | `embymedia.schedule_recording` service |
| **Cancel Recordings** | `embymedia.cancel_recording` service |
| **Series Timers** | Manage series recording rules |

```yaml
# Schedule a recording
service: embymedia.schedule_recording
target:
  entity_id: media_player.emby_living_room_tv
data:
  program_id: "142098"
  pre_padding_seconds: 60
  post_padding_seconds: 120
```

---

##  All the Services

### Playback Control
Standard `media_player.*` services work as expected: play, pause, stop, seek, volume, next/previous track.

### Emby-Specific Services

| Service | What it does |
|---------|--------------|
| `embymedia.send_message` | Display message on client screen |
| `embymedia.send_command` | Send navigation commands (Up, Down, Select, Back, Home) |
| `embymedia.mark_played` | Mark item as watched |
| `embymedia.mark_unplayed` | Mark item as unwatched |
| `embymedia.add_favorite` | Add to favorites |
| `embymedia.remove_favorite` | Remove from favorites |
| `embymedia.refresh_library` | Trigger library scan |
| `embymedia.play_instant_mix` | Start radio-style mix from any song/album/artist |
| `embymedia.play_similar` | Play similar content |
| `embymedia.clear_queue` | Clear playback queue |

### Playlist Management

| Service | What it does |
|---------|--------------|
| `embymedia.create_playlist` | Create new Audio or Video playlist |
| `embymedia.add_to_playlist` | Add items to playlist |
| `embymedia.remove_from_playlist` | Remove items from playlist |

### Collection Management

| Service | What it does |
|---------|--------------|
| `embymedia.create_collection` | Create a new collection |
| `embymedia.add_to_collection` | Add items to collection |
| `embymedia.remove_from_collection` | Remove items from collection |

### Live TV & DVR

| Service | What it does |
|---------|--------------|
| `embymedia.schedule_recording` | Schedule a one-time recording |
| `embymedia.cancel_recording` | Cancel a scheduled recording |
| `embymedia.cancel_series_timer` | Cancel a series recording rule |

### Server Administration

| Service | What it does |
|---------|--------------|
| `embymedia.run_scheduled_task` | Run any scheduled task |
| `embymedia.restart_server` | Restart Emby server ⚠️ |
| `embymedia.shutdown_server` | Shutdown Emby server ⚠️ |

<p align="center">
  <strong><a href="docs/SERVICES.md">📖 Complete Services Reference →</a></strong>
</p>

---

##  Media Browsing

Browse your entire library from Home Assistant:

| Library | Browse Options |
|---------|---------------|
| **Movies** | A-Z, Year, Decade, Genre, Studio, Collections, People, Tags |
| **TV Shows** | A-Z, Year, Decade, Genre, Studio → Series → Season → Episode |
| **Music** | Artists, Albums, Genres, Playlists (all with A-Z filtering) |
| **Live TV** | Channel listing |
| **Playlists** | All user playlists |
| **Collections** | All collections |

### Cast Emby Content Anywhere

The **Media Source** provider lets you play Emby content on ANY Home Assistant media player:

-  Cast to Chromecast
-  Stream to Sonos
-  Play on Google/Nest speakers
-  Send to any media_player entity

---

## 🐛 Troubleshooting

<details>
<summary><strong> Connection Failed</strong></summary>

1. Verify Emby is running: Open `http://your-server:8096` in browser
2. Check firewall allows the port
3. Try IP address instead of hostname
4. For HTTPS: Try disabling "Verify SSL"

</details>

<details>
<summary><strong> Invalid API Key</strong></summary>

1. Generate a **new** API key in Emby Dashboard
2. Check for extra spaces when pasting
3. Verify key hasn't been revoked

</details>

<details>
<summary><strong> No Entities Appearing</strong></summary>

1. Ensure an Emby client is **actively connected**
2. Verify device supports remote control
3. Check device isn't in "Ignored Devices" list
4. Check Home Assistant logs for errors

</details>

<details>
<summary><strong> WebSocket Disconnecting</strong></summary>

1. Check network stability
2. Try disabling WebSocket (falls back to polling)
3. Ensure no proxy is blocking WebSocket

</details>

### Get Diagnostics

1. **Settings** → **Devices & Services**
2. Find **Emby Media** → Click ⋮ → **Download Diagnostics**

Share the file when reporting issues (API keys are auto-redacted).

<p align="center">
  <strong><a href="docs/TROUBLESHOOTING.md">📖 Full Troubleshooting Guide →</a></strong>
</p>

---

##  Advanced Configuration

### Options (Settings → Devices & Services → Emby Media → Configure)

| Option | Default | Description |
|--------|---------|-------------|
| **Scan Interval** | 10s | Polling frequency (5-300s) |
| **WebSocket** | ✓ | Real-time updates |
| **Ignored Devices** | — | Hide specific clients |
| **Ignore Web Players** | ✗ | Hide browser sessions |
| **Direct Play** | ✓ | Try direct play first |
| **Video Container** | mp4 | Transcode format |
| **Prefix entities with "Emby"** | ✓ | Per-entity-type toggles |

### YAML Configuration (Optional)

For those who prefer YAML, basic connection settings can be imported:

```yaml
embymedia:
  host: emby.local
  api_key: !secret emby_api_key
```

> Advanced options are configured through the UI after initial setup.

<p align="center">
  <strong><a href="docs/CONFIGURATION.md">📖 Full Configuration Reference →</a></strong>
</p>

---

##  For Developers

### Entity Structure

Each Emby client creates multiple entities:

| Platform | Entity | Purpose |
|----------|--------|---------|
| `media_player` | `media_player.emby_*` | Playback control |
| `remote` | `remote.emby_*` | Navigation commands |
| `notify` | `notify.emby_*` | On-screen messages |
| `button` | `button.emby_*` | Server actions |
| `sensor` | `sensor.emby_*` | Server stats |
| `binary_sensor` | `binary_sensor.emby_*` | Server status |
| `image` | `image.emby_*` | Discovery cover art |

### Device Triggers

Available for automations:

- `playback_started` / `playback_stopped`
- `playback_paused` / `playback_resumed`
- `media_changed`
- `session_connected` / `session_disconnected`

### WebSocket Events

The integration fires custom events:

| Event | When |
|-------|------|
| `embymedia_library_updated` | Items added/removed/changed |
| `embymedia_user_data_changed` | Favorites, watched status, ratings |
| `embymedia_notification` | Server notifications |
| `embymedia_user_changed` | User account changes |

### Contributing

We welcome contributions! The project uses:

- **Python 3.13+**
- **Strict TDD** (100% test coverage required)
- **Strict typing** (no `Any` types)
- **mypy** + **ruff** for code quality

```bash
# Clone and setup
git clone https://github.com/holdestmade/homeassistant-emby.git
cd homeassistant-emby
pip install -r requirements_test.txt

# Run tests
pytest tests/ --cov=custom_components.embymedia

# Type check
mypy custom_components/embymedia/
```

---

##  Documentation

| Document | Description |
|----------|-------------|
| **[Installation](docs/INSTALLATION.md)** | Detailed setup instructions |
| **[Configuration](docs/CONFIGURATION.md)** | All options explained |
| **[Services](docs/SERVICES.md)** | Complete service reference |
| **[Automations](docs/AUTOMATIONS.md)** | 50+ ready-to-use examples |
| **[Troubleshooting](docs/TROUBLESHOOTING.md)** | Common issues & solutions |
| **[Changelog](CHANGELOG.md)** | Version history |
| **[Contributing](CONTRIBUTING.md)** | Development guidelines |

---

##  Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) — The incredible smart home platform
- [Emby](https://emby.media/) — Media server software
- The Home Assistant community for feedback and testing

---

