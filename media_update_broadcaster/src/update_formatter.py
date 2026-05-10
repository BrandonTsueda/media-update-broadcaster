from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable


DISCORD_LIMIT = 1900


@dataclass(frozen=True)
class ServiceProfile:
    name: str
    aliases: tuple[str, ...]
    purpose: str
    default_audience_impact: str
    github_repo: str | None = None
    homepage: str | None = None


@dataclass
class UpdateItem:
    service: str
    version: str
    title: str
    source: str
    published_at: str
    raw_notes: str
    category: str = "General"
    impact: str = ""
    highlights: list[str] = field(default_factory=list)


SERVICE_PROFILES: dict[str, ServiceProfile] = {
    "Sonarr": ServiceProfile(
        name="Sonarr",
        aliases=("sonarr",),
        purpose="TV show automation",
        default_audience_impact="TV episodes are found, upgraded, and organized more reliably.",
        github_repo="Sonarr/Sonarr",
        homepage="https://sonarr.tv/",
    ),
    "Radarr": ServiceProfile(
        name="Radarr",
        aliases=("radarr",),
        purpose="movie automation",
        default_audience_impact="Movies are searched, upgraded, and organized more reliably.",
        github_repo="Radarr/Radarr",
        homepage="https://radarr.video/",
    ),
    "Prowlarr": ServiceProfile(
        name="Prowlarr",
        aliases=("prowlarr",),
        purpose="indexer management",
        default_audience_impact="Search providers stay healthier, which helps requests find downloads faster.",
        github_repo="Prowlarr/Prowlarr",
        homepage="https://prowlarr.com/",
    ),
    "Overseerr": ServiceProfile(
        name="Overseerr",
        aliases=("overseerr", "seerr"),
        purpose="media request management",
        default_audience_impact="Requesting movies and shows should feel smoother and more dependable.",
        github_repo="sct/overseerr",
        homepage="https://overseerr.dev/",
    ),
    "Jellyseerr": ServiceProfile(
        name="Jellyseerr",
        aliases=("jellyseerr", "seerr"),
        purpose="Jellyfin request management",
        default_audience_impact="Jellyfin requests and approvals should be easier to manage.",
        github_repo="Fallenbagel/jellyseerr",
        homepage="https://github.com/Fallenbagel/jellyseerr",
    ),
    "Jellyfin": ServiceProfile(
        name="Jellyfin",
        aliases=("jellyfin",),
        purpose="media streaming",
        default_audience_impact="Playback, library browsing, and streaming stability should improve.",
        github_repo="jellyfin/jellyfin",
        homepage="https://jellyfin.org/",
    ),
    "SABnzbd": ServiceProfile(
        name="SABnzbd",
        aliases=("sabnzbd", "sabnzbdplus", "sab"),
        purpose="Usenet downloading",
        default_audience_impact="Downloads should be more stable, recover better, and complete more cleanly.",
        github_repo="sabnzbd/sabnzbd",
        homepage="https://sabnzbd.org/",
    ),
    "Bazarr": ServiceProfile(
        name="Bazarr",
        aliases=("bazarr",),
        purpose="subtitle automation",
        default_audience_impact="Subtitles should be found and synced more reliably.",
        github_repo="morpheus65535/bazarr",
        homepage="https://www.bazarr.media/",
    ),
    "Lidarr": ServiceProfile(
        name="Lidarr",
        aliases=("lidarr",),
        purpose="music automation",
        default_audience_impact="Music library matching and upgrades should be more reliable.",
        github_repo="Lidarr/Lidarr",
        homepage="https://lidarr.audio/",
    ),
    "Readarr": ServiceProfile(
        name="Readarr",
        aliases=("readarr",),
        purpose="book automation",
        default_audience_impact="Book and audiobook discovery should be more reliable.",
        github_repo="Readarr/Readarr",
        homepage="https://readarr.com/",
    ),
    "qBittorrent": ServiceProfile(
        name="qBittorrent",
        aliases=("qbittorrent", "qbit"),
        purpose="torrent downloading",
        default_audience_impact="Torrent downloads should behave more predictably.",
        github_repo="qbittorrent/qBittorrent",
        homepage="https://www.qbittorrent.org/",
    ),
    "Tautulli": ServiceProfile(
        name="Tautulli",
        aliases=("tautulli",),
        purpose="media usage monitoring",
        default_audience_impact="Watch history and server activity reporting should be more accurate.",
        github_repo="Tautulli/Tautulli",
        homepage="https://tautulli.com/",
    ),
}


IMPACT_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"\b(security|vulnerab|cve|auth|token|permission|privilege)\b", re.I), "Security", "Keeps the server and family access safer."),
    (re.compile(r"\b(fix|fixed|bug|crash|exception|error|fail|regression)\b", re.I), "Reliability", "Reduces crashes, failed requests, and weird edge-case behavior."),
    (re.compile(r"\b(performance|speed|faster|slow|memory|cpu|database|optimi[sz])\b", re.I), "Performance", "Should make the service feel quicker or lighter on the server."),
    (re.compile(r"\b(api|indexer|download|search|grab|import|metadata|scan)\b", re.I), "Automation", "Improves the behind-the-scenes automation that finds and organizes media."),
    (re.compile(r"\b(ui|ux|display|screen|page|layout|theme|accessibility)\b", re.I), "Usability", "Makes the app easier to use or understand."),
)


def clean_markdown(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def summarize_highlights(raw_notes: str, max_items: int = 5) -> list[str]:
    notes = clean_markdown(raw_notes)
    candidates: list[str] = []
    for line in notes.splitlines():
        line = re.sub(r"^[\s>*#\-+\d.)\[]+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if not line or len(line) < 12:
            continue
        if line.lower().startswith(("new:", "fixed:", "changed:", "added:", "bugfixes")):
            line = line.split(":", 1)[-1].strip()
        if line and line not in candidates:
            candidates.append(line)
    if not candidates and notes:
        candidates = [notes[:220].strip()]
    return [truncate(item, 180) for item in candidates[:max_items]]


def classify_update(raw_notes: str, service: str) -> tuple[str, str]:
    for pattern, category, impact in IMPACT_RULES:
        if pattern.search(raw_notes):
            return category, impact
    profile = SERVICE_PROFILES.get(service)
    if profile:
        return "General", profile.default_audience_impact
    return "General", "Keeps the media stack current and reduces surprise breakage."


def normalize_service(value: str) -> str:
    cleaned = value.strip()
    for profile in SERVICE_PROFILES.values():
        if cleaned.lower() == profile.name.lower() or cleaned.lower() in profile.aliases:
            return profile.name
    return cleaned or "Media Stack"


def build_update(
    *,
    service: str,
    version: str,
    title: str,
    source: str,
    published_at: str,
    raw_notes: str,
    impact_override: str = "",
) -> UpdateItem:
    normalized_service = normalize_service(service)
    category, impact = classify_update(raw_notes, normalized_service)
    return UpdateItem(
        service=normalized_service,
        version=version.strip() or "version not listed",
        title=title.strip() or "Media stack update",
        source=source.strip(),
        published_at=published_at.strip() or datetime.now(timezone.utc).date().isoformat(),
        raw_notes=clean_markdown(raw_notes),
        category=category,
        impact=impact_override.strip() or impact,
        highlights=summarize_highlights(raw_notes),
    )


def format_discord_message(updates: Iterable[UpdateItem], title: str, include_sources: bool = True) -> str:
    updates = list(updates)
    if not updates:
        return "No media stack updates were selected."

    generated = datetime.now().strftime("%b %d, %Y")
    lines = [
        f"**{title.strip() or 'Media Stack Update'}**",
        f"_Posted {generated}_",
        "",
        "Here is what changed in the media stack and why it matters:",
        "",
    ]

    for item in updates:
        lines.extend(
            [
                f"**{item.service} - {item.version}**",
                f"Impact: {item.impact}",
                f"Category: {item.category}",
            ]
        )
        if item.highlights:
            lines.append("Key changes:")
            lines.extend(f"- {highlight}" for highlight in item.highlights)
        if include_sources and item.source:
            lines.append(f"Source: {item.source}")
        lines.append("")

    lines.append("Bottom line: these updates help keep requests, downloads, and streaming reliable for everyone.")
    return "\n".join(lines).strip()


def split_for_discord(message: str, limit: int = DISCORD_LIMIT) -> list[str]:
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in message.split("\n\n"):
        paragraph_length = len(paragraph) + 2
        if current and current_length + paragraph_length > limit:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_length = 0
        if paragraph_length > limit:
            for line in paragraph.splitlines():
                if current and current_length + len(line) + 1 > limit:
                    chunks.append("\n".join(current).strip())
                    current = []
                    current_length = 0
                current.append(line)
                current_length += len(line) + 1
        else:
            current.append(paragraph)
            current_length += paragraph_length
    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."
