# Media Update Broadcaster

Media Update Broadcaster turns release notes for the media stack into clean Discord-ready update posts for family members.

It supports GitHub release fetching, manual update entry, post formatting, and local history. The app runs locally with Streamlit and stores saved history on disk.

## Run

```powershell
cd C:\dev\Repos\media-update-broadcaster
.\scripts\start-media-update-broadcaster.ps1
```

Open:

```text
http://localhost:8502
```

## Data

Saved batches are stored locally at:

```text
media_update_broadcaster\data\update_history.json
```

That file is ignored by git.
