# Emby Media Documentation

Welcome to the Emby Media for Home Assistant documentation.

---

## Getting Started

| Guide | Description |
|-------|-------------|
| **[Installation](INSTALLATION.md)** | Download, install, and verify the integration |
| **[Configuration](CONFIGURATION.md)** | Connect to Emby and customize settings |

---

## User Guides

| Guide | Description |
|-------|-------------|
| **[Automations](AUTOMATIONS.md)** | 50+ ready-to-use automation examples |
| **[Services](SERVICES.md)** | Complete reference for all service calls |
| **[Troubleshooting](TROUBLESHOOTING.md)** | Solutions for common issues |

---

## Technical Documentation

| Guide | Description |
|-------|-------------|
| **[Architecture](ARCHITECTURE.md)** | System design and component overview |
| **[Efficiency](EFFICIENCY.md)** | Performance best practices and tuning |

---

## Quick Reference

### Entities Created

| Platform | Entity Pattern | Purpose |
|----------|---------------|---------|
| `media_player` | `media_player.emby_*` | Playback control |
| `remote` | `remote.emby_*` | Navigation commands |
| `notify` | `notify.emby_*` | On-screen messages |
| `button` | `button.emby_*` | Server actions (refresh library, run library scan) |
| `sensor` | `sensor.emby_*` | Library & server stats |
| `binary_sensor` | `binary_sensor.emby_*` | Server status |
| `image` | `image.emby_*` | Discovery cover art |

### Key Services

| Service | Purpose |
|---------|---------|
| `embymedia.send_message` | Display on-screen message |
| `embymedia.send_command` | Remote navigation |
| `embymedia.mark_played` | Mark as watched |
| `embymedia.add_favorite` | Add to favorites |
| `embymedia.play_instant_mix` | Start radio mix |
| `embymedia.create_playlist` | Create playlist |
| `embymedia.schedule_recording` | DVR recording |

[Full services reference →](SERVICES.md)

### Sensors Available

**Server Health:**
- `binary_sensor.*_connected` — Server reachable?
- `binary_sensor.*_pending_restart` — Restart needed?
- `binary_sensor.*_update_available` — Update ready?
- `binary_sensor.*_library_scan_active` — Scan running?

**Library Counts:**
- `sensor.*_movies` / `sensor.*_tv_shows` / `sensor.*_episodes`
- `sensor.*_songs` / `sensor.*_albums` / `sensor.*_artists`

**Activity:**
- `sensor.*_active_sessions` — Connected clients
- `sensor.*_plugins` — Installed plugins
- `sensor.*_last_activity` — Recent activity

---

## Document Index

### User Documentation
- [INSTALLATION.md](INSTALLATION.md) — Installation guide
- [CONFIGURATION.md](CONFIGURATION.md) — Configuration reference
- [SERVICES.md](SERVICES.md) — Services reference
- [AUTOMATIONS.md](AUTOMATIONS.md) — Automation examples
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Problem solving

### Technical Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design overview
- [EFFICIENCY.md](EFFICIENCY.md) — Performance best practices

---

<p align="center">
  <a href="../README.md">← Back to Main README</a>
</p>
