from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class DiscordWebhookError(RuntimeError):
    """Raised when a Discord webhook URL or send attempt is invalid."""


@dataclass(frozen=True)
class DiscordSendResult:
    sent: int
    dry_run: bool


def validate_discord_webhook_url(url: str) -> str:
    candidate = url.strip()
    if not candidate:
        raise DiscordWebhookError("Discord webhook URL is required.")

    parsed = urlparse(candidate)
    allowed_hosts = {"discord.com", "discordapp.com"}
    if parsed.scheme != "https" or parsed.netloc not in allowed_hosts:
        raise DiscordWebhookError("Discord webhook URL must use https://discord.com or https://discordapp.com.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[:2] != ["api", "webhooks"]:
        raise DiscordWebhookError("Discord webhook URL must look like /api/webhooks/{id}/{token}.")

    return candidate


def send_discord_chunks(
    webhook_url: str,
    chunks: list[str],
    *,
    dry_run: bool = False,
    timeout: int = 12,
    max_retries: int = 2,
) -> DiscordSendResult:
    validated_url = validate_discord_webhook_url(webhook_url)
    non_empty_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    if not non_empty_chunks:
        raise DiscordWebhookError("There is no Discord message content to send.")

    if dry_run:
        return DiscordSendResult(sent=len(non_empty_chunks), dry_run=True)

    for index, chunk in enumerate(non_empty_chunks, start=1):
        _post_with_retry(validated_url, {"content": chunk}, timeout=timeout, max_retries=max_retries)
        if index < len(non_empty_chunks):
            time.sleep(0.6)

    return DiscordSendResult(sent=len(non_empty_chunks), dry_run=False)


def _post_with_retry(url: str, payload: dict[str, str], *, timeout: int, max_retries: int) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        request = Request(
            url,
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Bratsu-Media-Update-Broadcaster",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status in {200, 204}:
                    return
                raise DiscordWebhookError(f"Discord returned HTTP {response.status}.")
        except HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                time.sleep(_retry_after(exc) or (attempt + 1))
                last_error = exc
                continue
            raise DiscordWebhookError(f"Discord returned HTTP {exc.code}.") from exc
        except URLError as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(attempt + 1)
                continue
            raise DiscordWebhookError(f"Could not reach Discord: {exc.reason}") from exc

    raise DiscordWebhookError(f"Discord send failed: {last_error}")


def _retry_after(exc: HTTPError) -> float | None:
    value = exc.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(float(value), 0.5)
    except ValueError:
        return None
