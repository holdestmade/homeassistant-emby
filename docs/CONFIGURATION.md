# Configuration Reference

Everything you need to connect and customize your Emby Media integration.

---

## Quick Setup

### 1. Get Your API Key

1. Open Emby Server Dashboard: `http://your-server:8096`
2. **Settings** → **Advanced** → **API Keys**
3. Click **+ New API Key**
4. Name it "Home Assistant" → **OK**
5. **Copy the key** — you'll need it next

> **Tip:** Store your API key securely. Anyone with this key can control your Emby server.

### 2. Add the Integration

1. **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Emby Media"**
4. Enter your connection details (see table below)
5. Click **Submit**

---

## Connection Settings

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| **Host** | Yes | — | Emby server hostname or IP address |
| **Port** | Yes | 8096 | Server port number |
| **Use SSL** | | false | Enable for HTTPS connections |
| **API Key** | Yes | — | API key from Emby dashboard |
| **Verify SSL** | | true | Validate SSL certificate |

### Connection Examples

<table>
<tr>
<td width="33%">

**Local HTTP**
```
Host: 192.168.1.100
Port: 8096
Use SSL: unchecked
```

</td>
<td width="33%">

**Local HTTPS (self-signed)**
```
Host: emby.local
Port: 8920
Use SSL: checked
Verify SSL: unchecked
```

</td>
<td width="33%">

**Remote with SSL**
```
Host: emby.example.com
Port: 443
Use SSL: checked
Verify SSL: checked
```

</td>
</tr>
</table>

---

## Options (Post-Setup)

Change these anytime: **Settings** → **Devices & Services** → **Emby Media** → **Configure**

### Update Settings

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Scan Interval** | 10 | 5-300s | How often to poll for session updates |
| **Enable WebSocket** | Yes | — | Real-time updates (recommended) |
| **WebSocket Interval** | 1500 | 500-10000ms | Session subscription rate |
| **Library Scan Interval** | 1 hour | 1-24h | How often to update library counts |
| **Server Scan Interval** | 5 min | 5m-1h | How often to check server status |

**About Scan Interval:**
- Lower = more responsive, more server load
- With WebSocket enabled, polling drops to 60s (WebSocket handles real-time)
- Without WebSocket, this is your update frequency

**About Library Scan Interval:**
- Controls how often library statistics (movie count, etc.) are updated
- Lower values increase server load with minimal benefit
- Library changes via WebSocket trigger immediate refresh anyway

**About Server Scan Interval:**
- Controls how often server status (version, tasks) is checked
- 5 minutes is sufficient for most use cases
- Increase to 1 hour for low-power servers

**About WebSocket:**
- Near-instant state updates
- Auto-reconnects if disconnected
- Falls back to polling if unavailable
- **Recommended:** Keep enabled

> For detailed efficiency information, see **[Efficiency Best Practices](EFFICIENCY.md)**

### Device Filtering

| Option | Default | Description |
|--------|---------|-------------|
| **Ignored Devices** | — | Comma-separated list of device names to hide |
| **Ignore Web Players** | No | Hide all browser-based sessions |

**Example:**
```
Guest iPad, Kids Tablet, Web Player
```

### Entity Naming

| Option | Default | Description |
|--------|---------|-------------|
| **Prefix Emby device names with "Emby"** | Yes | Add "Emby" prefix to Emby client device names |

**With prefix ON:** `media_player.emby_living_room_tv`
**With prefix OFF:** `media_player.living_room_tv`

Each Emby client is one device in Home Assistant, shared by its media
player, remote and notify entities, so the prefix is a single setting for
that device rather than one per platform. Entity IDs are derived from the
device name, so they follow the same setting.

Changing this affects newly discovered devices. Entities that already exist
keep their current entity IDs, which protects existing automations and
dashboards; rename them from the entity settings if you want them updated.

Earlier versions offered four separate prefix options
(`prefix_media_player`, `prefix_notify`, `prefix_remote` and
`prefix_button`). They are replaced automatically when the integration
first loads, carrying over the media player setting.

### Discovery Sensors

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Enable Discovery Sensors** | Yes | — | Next Up, Continue Watching, Recently Added and Suggestions |
| **Discovery Scan Interval** | 900 | 300-3600s | How often discovery data refreshes |

Discovery sensors are created per Emby user, so a server with several users
produces several sets. Turn them off if you only want playback control, which
also removes their polling entirely.

Each sensor exposes an `items` attribute holding the list of media, with an
`image_url` for artwork:

```jinja
{{ state_attr('sensor.emby_next_up', 'items')[0].name }}
{{ state_attr('sensor.emby_next_up', 'items')[0].image_url }}
```

### Transcoding Options

| Option | Default | Description |
|--------|---------|-------------|
| **Direct Play** | Yes | Try direct play before transcoding |
| **Transcoding Profile** | universal | Device profile used when transcoding |
| **Video Container** | mp4 | Container format: mp4, mkv, webm |
| **Max Video Bitrate** | — | Limit video bitrate (kbps) |
| **Max Audio Bitrate** | — | Limit audio bitrate (kbps) |

**Transcoding Profile:**
- `universal` — Safe defaults that suit most clients
- `chromecast` — Tuned for Chromecast targets
- `roku` — Tuned for Roku devices
- `appletv` — Tuned for Apple TV
- `audio_only` — Audio streams only, for speaker targets

**Video Container:**
- `mp4` — Most compatible, works everywhere
- `mkv` — Better quality, less compatible
- `webm` — Web-optimized, limited support

**Bitrate Guidelines:**

| Quality | Video (kbps) | Audio (kbps) |
|---------|-------------|--------------|
| 1080p High | 10000-15000 | 320 |
| 1080p Medium | 6000-8000 | 256 |
| 720p | 4000-5000 | 192 |
| Mobile | 2000-3000 | 128 |

---

## YAML Configuration (Optional)

The integration supports YAML configuration for initial setup, which is then imported into the UI-based config entry. Most users should use the UI configuration above instead.

> **Note:** YAML imports connection settings only. Advanced options (device filtering, transcoding, entity prefixes) must be configured through **Settings** → **Devices & Services** → **Emby Media** → **Configure** after setup.

### Basic YAML Setup

**configuration.yaml:**
```yaml
embymedia:
  host: emby.local
  api_key: !secret emby_api_key
  port: 8096        # Optional, default: 8096
  ssl: false        # Optional, default: false
  verify_ssl: true  # Optional, default: true
```

**secrets.yaml:**
```yaml
emby_api_key: your-api-key-here
```

After restarting Home Assistant, the YAML configuration is imported as a config entry. You can then modify advanced options through the UI.

---

## Multiple Emby Servers

Add the integration multiple times for multiple servers:

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search **"Emby Media"**
3. Enter second server's details

Each server creates its own set of entities.

---

## User Selection

If your Emby server has multiple users:

1. During setup, you may be prompted to select a user
2. This affects which libraries are visible
3. User-specific restrictions apply

If no user is selected, API key permissions apply.

---

## Troubleshooting Configuration

### "Connection Failed"

1. Verify Emby is running: `http://your-server:8096`
2. Check firewall allows the port
3. Try IP address instead of hostname
4. For HTTPS, try disabling "Verify SSL"

### "Invalid API Key"

1. Generate a **new** key in Emby Dashboard
2. Check for extra spaces when pasting
3. Verify key hasn't been revoked

### "No Devices Found"

1. Open Emby on at least one client device
2. Ensure device supports remote control
3. Check device isn't in "Ignored Devices" list

### Changes Not Taking Effect

- UI changes apply immediately
- YAML changes require Home Assistant restart
- Reload integration: **Emby Media** → ⋮ → **Reload**

---

## Next Steps

- **[Services](SERVICES.md)** — Available service calls
- **[Automations](AUTOMATIONS.md)** — Ready-to-use automation examples
- **[Troubleshooting](TROUBLESHOOTING.md)** — Detailed problem solving
