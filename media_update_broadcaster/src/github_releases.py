from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .update_formatter import SERVICE_PROFILES, UpdateItem, build_update


class ReleaseFetchError(RuntimeError):
    """Raised when a release feed cannot be fetched or parsed."""


def fetch_latest_release(service_name: str, timeout: int = 15) -> UpdateItem:
    profile = SERVICE_PROFILES[service_name]
    if not profile.github_repo:
        raise ReleaseFetchError(f"{service_name} does not have a configured GitHub release source.")

    url = f"https://api.github.com/repos/{profile.github_repo}/releases/latest"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Bratsu-Media-Update-Broadcaster",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ReleaseFetchError(f"GitHub returned HTTP {exc.code} for {service_name}.") from exc
    except URLError as exc:
        raise ReleaseFetchError(f"Could not reach GitHub for {service_name}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseFetchError(f"GitHub returned unreadable release data for {service_name}.") from exc

    published_at = payload.get("published_at") or payload.get("created_at") or ""
    if published_at:
        published_at = _friendly_date(published_at)

    return build_update(
        service=service_name,
        version=payload.get("tag_name") or payload.get("name") or "latest",
        title=payload.get("name") or f"{service_name} release",
        source=payload.get("html_url") or url,
        published_at=published_at,
        raw_notes=payload.get("body") or "No release notes were provided by the project.",
    )


def _friendly_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value
