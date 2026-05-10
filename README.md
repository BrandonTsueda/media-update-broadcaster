# Media Update Broadcaster

Media Update Broadcaster turns media-stack release notes into clean Discord-ready update posts for family members. It is built for self-hosted media admins who want to explain what changed without pasting raw changelogs into chat.

## What It Does

- Fetches latest public GitHub releases for common media services.
- Accepts manual update notes for Docker image pulls, maintenance windows, or custom apps.
- Summarizes user-facing impact and key changes.
- Splits long messages before Discord's message limit.
- Sends directly to Discord through a validated webhook, with dry-run mode on by default.
- Saves local post history without committing private history to Git.

## Supported Services

Sonarr, Radarr, Prowlarr, Overseerr, Jellyseerr, Jellyfin, SABnzbd, Bazarr, Lidarr, Readarr, qBittorrent, Tautulli, and custom services.

## Quick Start

```powershell
cd C:\dev\Repos\media-update-broadcaster
.\scripts\start-media-update-broadcaster.ps1
```

Open:

```text
http://localhost:8502
```

## Discord Webhook Setup

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Then set:

```text
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

The app also accepts a webhook pasted into the UI. Dry run is enabled by default so the first click validates formatting without posting.

## Data And Secrets

Saved batches are stored locally at:

```text
media_update_broadcaster\data\update_history.json
```

That file is ignored by git.

Do not commit Discord webhook URLs, Streamlit secrets, or generated history files.

## Verification

```powershell
cd C:\dev\Repos\media-update-broadcaster
python -m compileall -q media_update_broadcaster scripts
```

## Roadmap

- Add scheduled release checks for selected services.
- Add configurable audience templates.
- Add optional Discord embeds once plain-text posting is fully stable.
