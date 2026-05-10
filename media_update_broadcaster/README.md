# Media Update Broadcaster

Media Update Broadcaster turns release notes for the media stack into clean Discord posts for family members.

It supports:

- Sonarr
- Radarr
- Prowlarr
- Overseerr / Jellyseerr
- Jellyfin
- SABnzbd
- Bazarr
- Lidarr
- Readarr
- qBittorrent
- Tautulli
- Custom services

## Quick Start

```powershell
cd "C:\dev\Repos\media-update-broadcaster"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r media_update_broadcaster\requirements.txt
streamlit run media_update_broadcaster\main.py --server.port 8502
```

Open:

```text
http://localhost:8502
```

## Workflow

1. Use **Fetch Releases** to pull the latest public GitHub release notes for supported services.
2. Use **Paste Update** for Docker image notes, app changelogs, manual maintenance notes, or any service not listed.
3. Review **Discord Output** and paste the generated chunk into the family Discord.
4. Save useful posts to **History** for local reference.

## Data

Saved batches are stored locally:

```text
media_update_broadcaster\data\update_history.json
```

The app does not send your saved history anywhere.
