# Integration Comparison Matrix

## Home Assistant Media Server Integrations

This document provides a comprehensive comparison between this custom Emby Media integration (`embymedia`) and the official Home Assistant core integrations for Emby and Plex.

**Last Updated:** January 2026

**Sources:**

- [Official Emby Integration](https://www.home-assistant.io/integrations/emby/) (HA Core)
- [Official Plex Integration](https://www.home-assistant.io/integrations/plex/) (HA Core)
- This repository's source code

---

## Executive Summary

| Aspect               | embymedia (This)   | Official Emby | Official Plex |
| -------------------- | ------------------ | ------------- | ------------- |
| **Status**           | Active Development | Legacy        | Active        |
| **Entity Platforms** | 6                  | 1             | 4             |
| **Services**         | 20+                | 0             | 1             |
| **Config Flow**      | Yes Full            | No YAML Only  | Yes Full       |
| **WebSocket**        | Yes Real-time       | No Polling    | Yes Real-time  |
| **Voice Assist**     | Yes search_media    | No            | No            |
| **Quality**          | Modern (2025)      | Legacy        | Modern        |

---

## Configuration & Setup

| Feature                    | embymedia        | Official Emby | Official Plex          |
| -------------------------- | ---------------- | ------------- | ---------------------- |
| **Config Flow (UI Setup)** | Yes Full          | No YAML only  | Yes Full                |
| **Options Flow**           | Yes Extensive     | No            | Yes Limited             |
| **Reauth Flow**            | Yes               | No            | Yes                     |
| **SSDP Discovery**         | No               | No            | No                     |
| **Zeroconf Discovery**     | No               | No            | Yes                     |
| **GDM Discovery**          | N/A              | N/A           | Yes                     |
| **OAuth Authentication**   | No (API Key)     | No (API Key)  | Yes (plex.tv)           |
| **Multi-Server Support**   | Yes               | Partial (Manual)     | Yes                     |
| **Multi-User Support**     | Yes Per-user data | No            | Yes Per-user monitoring |
| **SSL/TLS Support**        | Yes Configurable  | Yes Basic      | Yes Full                |
| **Verify SSL Option**      | Yes               | No            | Yes                     |

### Configuration Options Comparison

| Option                | embymedia       | Official Emby | Official Plex |
| --------------------- | --------------- | ------------- | ------------- |
| Host/Port/API Key     | Yes              | Yes            | Yes            |
| Polling Interval      | Yes 5-300s       | No Fixed      | No Fixed      |
| Library Scan Interval | Yes 1-24h        | No            | No            |
| WebSocket Toggle      | Yes              | N/A           | No Always on  |
| Ignored Devices       | Yes              | No            | No            |
| Ignore Web Players    | Yes              | No            | Yes            |
| Entity Prefix Control | Yes Per-platform | No            | No            |
| Transcoding Settings  | Yes Full         | No            | No            |
| Monitored Users       | Yes              | No            | Yes            |
| Episode Artwork       | N/A             | N/A           | Yes            |

---

## Entity Platforms

| Platform          | embymedia        | Official Emby  | Official Plex   |
| ----------------- | ---------------- | -------------- | --------------- |
| **Media Player**  | Yes Per-session   | Yes Per-session | Yes Per-client   |
| **Sensor**        | Yes 15+ types     | No             | Yes 2 types      |
| **Binary Sensor** | Yes 5 types       | No             | No              |
| **Remote**        | Yes Navigation    | No             | No              |
| **Button**        | Yes Multiple      | No             | Yes Scan clients |
| **Notify**        | Yes On-screen     | No             | No              |
| **Image**         | Yes Discovery art | No             | No              |
| **Update**        | No               | No             | Yes              |

### Sensor Types Detail

| Sensor Type       | embymedia | Official Emby | Official Plex         |
| ----------------- | --------- | ------------- | --------------------- |
| Active Sessions   | Yes        | No            | Yes ("watching")       |
| Movie Count       | Yes        | No            | Yes                    |
| Series Count      | Yes        | No            | Yes (as shows)         |
| Episode Count     | Yes        | No            | Yes                    |
| Song Count        | Yes        | No            | No                    |
| Album Count       | Yes        | No            | Yes                    |
| Artist Count      | Yes        | No            | Yes                    |
| Collection Count  | Yes        | No            | No                    |
| Playlist Count    | Yes        | No            | No                    |
| Server Version    | Yes        | No            | No (in Update entity) |
| Running Tasks     | Yes        | No            | No                    |
| Recording Count   | Yes        | No            | No                    |
| Connected Devices | Yes        | No            | No                    |
| Plugin Count      | Yes        | No            | No                    |
| Watch Statistics  | Yes        | No            | No                    |
| Last Added Title  | No        | No            | Yes                    |

### Binary Sensor Types

| Binary Sensor       | embymedia | Official Emby | Official Plex    |
| ------------------- | --------- | ------------- | ---------------- |
| Server Connected    | Yes        | No            | No               |
| Pending Restart     | Yes        | No            | No               |
| Update Available    | Yes        | No            | No (uses Update) |
| Library Scan Active | Yes        | No            | No               |
| Live TV Enabled     | Yes        | No            | N/A              |

---

## Media Player Capabilities

### Playback Control

| Feature        | embymedia | Official Emby | Official Plex |
| -------------- | --------- | ------------- | ------------- |
| Play           | Yes        | Yes            | Yes            |
| Pause          | Yes        | Yes            | Yes            |
| Stop           | Yes        | Yes            | Yes            |
| Next Track     | Yes        | Yes            | Yes            |
| Previous Track | Yes        | Yes            | Yes            |
| Seek           | Yes        | Yes            | Yes            |
| Volume Set     | Yes        | No            | Yes            |
| Volume Mute    | Yes        | No            | Partial (Simulated)  |
| Shuffle Set    | Yes        | No            | No            |
| Repeat Set     | Yes        | No            | No            |

### Media Selection

| Feature        | embymedia       | Official Emby | Official Plex |
| -------------- | --------------- | ------------- | ------------- |
| Play Media     | Yes              | No            | Yes            |
| Browse Media   | Yes              | No            | Yes            |
| Search Media   | Yes Voice Assist | No            | No            |
| Media Enqueue  | Yes              | No            | No            |
| Clear Playlist | Yes              | No            | No            |

### Media Information

| Property              | embymedia | Official Emby | Official Plex |
| --------------------- | --------- | ------------- | ------------- |
| Title                 | Yes        | Yes            | Yes            |
| Duration              | Yes        | Yes            | Yes            |
| Position              | Yes        | Yes            | Yes            |
| Artwork               | Yes        | Yes            | Yes            |
| Series/Season/Episode | Yes        | Yes            | Yes            |
| Album/Artist          | Yes        | Yes            | Yes            |
| Content ID            | Yes        | Yes            | Yes            |
| User/App Name         | Yes        | Yes            | Yes            |

### Supported Media Types

| Media Type   | embymedia | Official Emby | Official Plex |
| ------------ | --------- | ------------- | ------------- |
| Movies       | Yes        | Yes            | Yes            |
| TV Episodes  | Yes        | Yes            | Yes            |
| Music Tracks | Yes        | Yes            | Yes            |
| Music Videos | Yes        | Yes            | No            |
| Photos       | Yes        | No            | Yes            |
| Live TV      | Yes        | Yes            | N/A           |
| Trailers     | Yes        | Yes            | Yes (clips)    |
| Playlists    | Yes        | No            | Yes            |

---

## Services

### Playback Services

| Service          | embymedia | Official Emby | Official Plex |
| ---------------- | --------- | ------------- | ------------- |
| Send Message     | Yes        | No            | No            |
| Send Command     | Yes        | No            | No            |
| Mark Played      | Yes        | No            | No            |
| Mark Unplayed    | Yes        | No            | No            |
| Add Favorite     | Yes        | No            | No            |
| Remove Favorite  | Yes        | No            | No            |
| Play Instant Mix | Yes        | No            | No            |
| Play Similar     | Yes        | No            | No            |
| Clear Queue      | Yes        | No            | No            |

### Library Services

| Service                | embymedia | Official Emby | Official Plex |
| ---------------------- | --------- | ------------- | ------------- |
| Refresh Library        | Yes        | No            | Yes            |
| Create Playlist        | Yes        | No            | No            |
| Add to Playlist        | Yes        | No            | No            |
| Remove from Playlist   | Yes        | No            | No            |
| Create Collection      | Yes        | No            | No            |
| Add to Collection      | Yes        | No            | No            |
| Remove from Collection | Yes        | No            | No            |

### Live TV Services

| Service             | embymedia | Official Emby | Official Plex |
| ------------------- | --------- | ------------- | ------------- |
| Schedule Recording  | Yes        | No            | N/A           |
| Cancel Recording    | Yes        | No            | N/A           |
| Cancel Series Timer | Yes        | No            | N/A           |

### Server Administration

| Service            | embymedia | Official Emby | Official Plex |
| ------------------ | --------- | ------------- | ------------- |
| Run Scheduled Task | Yes        | No            | No            |
| Restart Server     | Yes        | No            | No            |
| Shutdown Server    | Yes        | No            | No            |

---

## Real-Time Updates

| Feature               | embymedia              | Official Emby | Official Plex |
| --------------------- | ---------------------- | ------------- | ------------- |
| WebSocket Support     | Yes Full                | No            | Yes Limited    |
| Session Updates       | Yes Real-time           | Polling       | Yes Real-time  |
| Library Changes       | Yes Real-time           | No            | Yes Signals    |
| User Data Changes     | Yes Real-time           | No            | No            |
| Auto-Reconnection     | Yes Exponential backoff | N/A           | Yes            |
| Adaptive Polling      | Yes WS-aware            | No            | No            |
| Configurable Interval | Yes 500-10000ms         | No            | No            |

---

## Media Browsing

| Feature                 | embymedia | Official Emby | Official Plex |
| ----------------------- | --------- | ------------- | ------------- |
| Browse Media Support    | Yes        | No            | Yes            |
| Hierarchical Navigation | Yes        | No            | Yes            |
| Libraries               | Yes        | No            | Yes            |
| Genres                  | Yes        | No            | No            |
| Artists/Albums          | Yes        | No            | Yes            |
| Series/Seasons          | Yes        | No            | Yes            |
| Playlists               | Yes        | No            | Yes            |
| Collections/BoxSets     | Yes        | No            | No            |
| Recommendations         | Yes        | No            | Yes (Hubs)     |

---

## Voice Assistant Integration

| Feature                 | embymedia | Official Emby | Official Plex |
| ----------------------- | --------- | ------------- | ------------- |
| HA Assist Support       | Yes        | No            | No            |
| search_media Method     | Yes        | No            | No            |
| Natural Language Search | Yes        | No            | No            |
| Play by Voice           | Yes        | No            | No            |

---

## Device Automation

| Feature                | embymedia  | Official Emby | Official Plex |
| ---------------------- | ---------- | ------------- | ------------- |
| **Device Triggers**    | Yes 7 types | No            | No            |
| - playback_started     | Yes         | No            | No            |
| - playback_stopped     | Yes         | No            | No            |
| - playback_paused      | Yes         | No            | No            |
| - playback_resumed     | Yes         | No            | No            |
| - media_changed        | Yes         | No            | No            |
| - session_connected    | Yes         | No            | No            |
| - session_disconnected | Yes         | No            | No            |
| **Device Conditions**  | Yes 5 types | No            | No            |
| - is_playing           | Yes         | No            | No            |
| - is_paused            | Yes         | No            | No            |
| - is_idle              | Yes         | No            | No            |
| - is_off               | Yes         | No            | No            |
| - has_media            | Yes         | No            | No            |

---

## Remote Entity (Navigation)

| Command                         | embymedia | Official Emby | Official Plex |
| ------------------------------- | --------- | ------------- | ------------- |
| Navigation (Up/Down/Left/Right) | Yes        | No            | No            |
| Page Up/Down                    | Yes        | No            | No            |
| Select/Back                     | Yes        | No            | No            |
| Home/Settings                   | Yes        | No            | No            |
| Context Menu                    | Yes        | No            | No            |
| OSD Menu                        | Yes        | No            | No            |
| Volume Keys                     | Yes        | No            | No            |
| Audio/Subtitle Index            | Yes        | No            | No            |
| Send String                     | Yes        | No            | No            |
| Screenshot                      | Yes        | No            | No            |

---

## Discovery & Recommendations

| Feature            | embymedia         | Official Emby | Official Plex  |
| ------------------ | ----------------- | ------------- | -------------- |
| Next Up Episodes   | Yes Sensor + Image | No            | No             |
| Continue Watching  | Yes Sensor + Image | No            | No             |
| Recently Added     | Yes Sensor + Image | No            | Yes (attribute) |
| Suggestions        | Yes Sensor + Image | No            | No             |
| Per-User Discovery | Yes                | No            | No             |

---

## Transcoding & Streaming

| Feature                  | embymedia        | Official Emby | Official Plex |
| ------------------------ | ---------------- | ------------- | ------------- |
| Direct Play Preference   | Yes Configurable  | N/A           | N/A           |
| Transcode Profiles       | Yes 5 presets     | No            | No            |
| - Universal              | Yes               | No            | No            |
| - Chromecast             | Yes               | No            | No            |
| - Roku                   | Yes               | No            | No            |
| - Apple TV               | Yes               | No            | No            |
| - Audio Only             | Yes               | No            | No            |
| Max Bitrate Config       | Yes Video + Audio | No            | No            |
| Container Selection      | Yes mp4/mkv/webm  | No            | No            |
| HLS Streaming            | Yes               | No            | No            |
| PlaybackInfo Negotiation | Yes               | No            | No            |

---

## Live TV & DVR

| Feature                  | embymedia | Official Emby | Official Plex |
| ------------------------ | --------- | ------------- | ------------- |
| Live TV Channel Browse   | Yes        | Partial (Basic)      | N/A           |
| Recording Management     | Yes        | No            | N/A           |
| Series Timers            | Yes        | No            | N/A           |
| Active Recordings Sensor | Yes        | No            | N/A           |
| Scheduled Timers Sensor  | Yes        | No            | N/A           |

---

## Architecture & Quality

| Aspect                | embymedia          | Official Emby    | Official Plex |
| --------------------- | ------------------ | ---------------- | ------------- |
| Quality Scale         | Modern             | Legacy           | Modern        |
| IoT Class             | local_push         | local_push       | local_push    |
| Integration Type      | Hub                | Platform         | Service       |
| Coordinators          | Yes Multi (4 types) | No               | Partial (Limited)    |
| Request Coalescing    | Yes                 | No               | No            |
| Browse Caching        | Yes                 | No               | No            |
| Diagnostics Export    | Yes                 | No               | No            |
| Device ID Persistence | Yes                 | Partial (Session-based) | Yes            |

### Coordinator Types (embymedia)

| Coordinator | Purpose                       | Default Interval |
| ----------- | ----------------------------- | ---------------- |
| Session     | Active sessions/players       | 10 seconds       |
| Server      | Server status, tasks, plugins | 5 minutes        |
| Library     | Item counts, virtual folders  | 1 hour           |
| Discovery   | Next Up, Continue Watching    | 15 minutes       |

---

## Third-Party Integration

| Feature       | embymedia       | Official Emby | Official Plex |
| ------------- | --------------- | ------------- | ------------- |
| Sonos Support | No              | No            | Yes Direct     |
| Cast Support  | Partial (Via profiles) | No            | Yes            |
| Media Source  | Yes              | No            | Yes            |

---

## Error Handling & Resilience

| Feature               | embymedia          | Official Emby | Official Plex  |
| --------------------- | ------------------ | ------------- | -------------- |
| Connection Recovery   | Yes Auto-reconnect  | Basic         | Yes             |
| Auth Error Handling   | Yes Reauth flow     | No            | Yes Reauth flow |
| SSL Error Handling    | Yes Configurable    | Basic         | Yes             |
| Timeout Configuration | Yes                 | No            | No             |
| Health Checks         | Yes 5-min intervals | No            | No             |
| Stale Session Cleanup | Yes                 | No            | No             |

---

## Summary

### embymedia (This Integration)

**Strengths:**

- Most comprehensive Emby integration available
- Full config flow with extensive options
- Real-time WebSocket updates with adaptive polling
- 6 entity platforms providing complete control
- 20+ services for playback, library, and server management
- Voice assistant (Assist) integration via search_media
- Device triggers and conditions for automations
- Remote entity for navigation control
- Discovery sensors with artwork (Next Up, Continue Watching)
- Transcoding profile support
- Live TV and DVR capabilities
- Modern architecture with multiple specialized coordinators

**Use When:**

- You want the most complete Emby experience in Home Assistant
- You need voice control via Home Assistant Assist
- You want device triggers for playback automations
- You need remote control navigation
- You want real-time notifications of library changes
- You use Live TV features

### Official Emby (HA Core)

**Strengths:**

- Part of Home Assistant Core (no custom component needed)
- Simple, lightweight implementation
- Basic playback control

**Limitations:**

- Legacy status, minimal maintenance
- YAML configuration only
- No config flow or options
- Single platform (media_player only)
- No volume, shuffle, repeat, browse, or search
- No services
- No sensors or binary sensors
- No WebSocket/real-time updates

**Use When:**

- You only need basic play/pause/stop functionality
- You prefer not to install custom components
- You have very simple automation needs

### Official Plex (HA Core)

**Strengths:**

- Part of Home Assistant Core
- Full config flow with OAuth
- Zeroconf auto-discovery
- WebSocket real-time updates
- Media browsing support
- Library sensors
- Update entity for server updates
- Sonos integration
- Good media information display

**Limitations:**

- No shuffle or repeat control
- No voice assistant integration
- No device triggers or conditions
- No remote entity for navigation
- No playlist/queue management
- Limited services (refresh_library only)
- Volume mute is simulated

**Use When:**

- You use Plex Media Server
- You want official HA Core support
- You need Sonos integration
- You want auto-discovery

---

## Feature Count Summary

| Category              | embymedia | Official Emby | Official Plex |
| --------------------- | --------- | ------------- | ------------- |
| Entity Platforms      | 6         | 1             | 4             |
| Media Player Features | 15        | 6             | 10            |
| Services              | 20+       | 0             | 1             |
| Sensor Types          | 15+       | 0             | 2             |
| Binary Sensors        | 5         | 0             | 0             |
| Device Triggers       | 7         | 0             | 0             |
| Device Conditions     | 5         | 0             | 0             |
| Remote Commands       | 15+       | 0             | 0             |
| Config Options        | 20+       | 4             | 5             |
| Coordinators          | 4         | 0             | 1             |

---

_This comparison was generated by analyzing the source code of all three integrations as of January 2026._
