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
| **Host** | ✓ | — | Emby server hostname or IP address |
| **Port** | ✓ | 8096 | Server port number |
| **Use SSL** | | false | Enable for HTTPS connections |
| **API Key** | ✓ | — | API key from Emby dashboard |
| **Verify SSL** | | true | Validate SSL certificate |

### Connection Examples

<table>
<tr>
<td width="33%">

**Local HTTP**
```
Host: 192.168.1.100
Port: 8096
Use SSL: ☐
```

</td>
<td width="33%">

**Local HTTPS (self-signed)**
```
Host: emby.local
Port: 8920
Use SSL: ☑
Verify SSL: ☐
```

</td>
<td width="33%">

**Remote with SSL**
```
Host: emby.example.com
Port: 443
Use SSL: ☑
Verify SSL: ☑
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
| **Enable WebSocket** | ✓ | — | Real-time updates (recommended) |
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
| **Ignore Web Players** | ✗ | Hide all browser-based sessions |

**Example:**
```
Guest iPad, Kids Tablet, Web Player
```

### Entity Naming

| Option | Default | Description |
|--------|---------|-------------|
| **Prefix Media Players** | ✓ | Add "Emby" prefix to media player names |
| **Prefix Remote** | ✓ | Add "Emby" prefix to remote entity names |
| **Prefix Notify** | ✓ | Add "Emby" prefix to notify entity names |
| **Prefix Button** | ✓ | Add "Emby" prefix to button entity names |

**With prefix ON:** `media_player.emby_living_room_tv`
**With prefix OFF:** `media_player.living_room_tv`

### Transcoding Options

| Option | Default | Description |
|--------|---------|-------------|
| **Direct Play** | ✓ | Try direct play before transcoding |
| **Video Container** | mp4 | Container format: mp4, mkv, webm |
| **Max Video Bitrate** | — | Limit video bitrate (kbps) |
| **Max Audio Bitrate** | — | Limit audio bitrate (kbps) |

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

1. ✓ Verify Emby is running: `http://your-server:8096`
2. ✓ Check firewall allows the port
3. ✓ Try IP address instead of hostname
4. ✓ For HTTPS, try disabling "Verify SSL"

### "Invalid API Key"

1. ✓ Generate a **new** key in Emby Dashboard
2. ✓ Check for extra spaces when pasting
3. ✓ Verify key hasn't been revoked

### "No Devices Found"

1. ✓ Open Emby on at least one client device
2. ✓ Ensure device supports remote control
3. ✓ Check device isn't in "Ignored Devices" list

### Changes Not Taking Effect

- UI changes apply immediately
- YAML changes require Home Assistant restart
- Reload integration: **Emby Media** → ⋮ → **Reload**

---

## Next Steps

- **[Services](SERVICES.md)** — Available service calls
- **[Automations](AUTOMATIONS.md)** — Ready-to-use automation examples
- **[Troubleshooting](TROUBLESHOOTING.md)** — Detailed problem solving
