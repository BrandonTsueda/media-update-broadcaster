from __future__ import annotations

import sys
import os
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.discord_client import DiscordWebhookError, send_discord_chunks, validate_discord_webhook_url
from src.github_releases import ReleaseFetchError, fetch_latest_release
from src.storage import load_history, save_batch
from src.update_formatter import (
    SERVICE_PROFILES,
    UpdateItem,
    build_update,
    format_discord_message,
    split_for_discord,
)

PROJECT_ROOT = APP_DIR.parent


st.set_page_config(
    page_title="Media Update Broadcaster",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_dotenv() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
            continue
        key, value = cleaned.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def configured_webhook_url() -> str:
    secret_value = ""
    try:
        secret_value = str(st.secrets.get("DISCORD_WEBHOOK_URL", ""))
    except Exception:
        secret_value = ""
    return os.environ.get("DISCORD_WEBHOOK_URL", "").strip() or secret_value.strip()


def init_state() -> None:
    st.session_state.setdefault("updates", [])


def add_update(update: UpdateItem) -> None:
    st.session_state.updates.append(update)


def render_update_card(update: UpdateItem, index: int) -> None:
    with st.container(border=True):
        left, right = st.columns([0.75, 0.25])
        with left:
            st.markdown(f"**{update.service} - {update.version}**")
            st.caption(f"{update.category} | {update.published_at}")
            st.write(update.impact)
            for highlight in update.highlights:
                st.markdown(f"- {highlight}")
        with right:
            if st.button("Remove", key=f"remove-{index}", use_container_width=True):
                st.session_state.updates.pop(index)
                st.rerun()


def main() -> None:
    load_dotenv()
    init_state()

    st.title("Media Update Broadcaster")
    st.caption("Turn media-stack release notes into family-friendly Discord updates.")

    with st.sidebar:
        st.header("Stack Sources")
        st.write("Built-in services")
        for profile in SERVICE_PROFILES.values():
            source = profile.github_repo or profile.homepage or "manual"
            st.caption(f"{profile.name}: {source}")
        st.divider()
        if st.button("Clear current batch", use_container_width=True):
            st.session_state.updates = []
            st.rerun()

    source_tab, manual_tab, output_tab, history_tab = st.tabs(
        ["Fetch Releases", "Paste Update", "Discord Output", "History"]
    )

    with source_tab:
        st.subheader("Pull Latest GitHub Releases")
        st.write("Select services, fetch the latest public release notes, then review the generated impact summary.")
        services = st.multiselect(
            "Services",
            options=list(SERVICE_PROFILES.keys()),
            default=["Sonarr", "Radarr", "Prowlarr", "Jellyfin", "SABnzbd"],
        )
        if st.button("Fetch selected releases", type="primary"):
            successes = 0
            for service in services:
                try:
                    add_update(fetch_latest_release(service))
                    successes += 1
                except ReleaseFetchError as exc:
                    st.warning(str(exc))
            if successes:
                st.success(f"Added {successes} update(s) to the current batch.")

    with manual_tab:
        st.subheader("Paste Release Notes")
        with st.form("manual-update-form", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox(
                    "Service",
                    options=[*SERVICE_PROFILES.keys(), "Other"],
                    index=0,
                )
                custom_service = ""
                if service == "Other":
                    custom_service = st.text_input("Custom service name")
                version = st.text_input("Version or update label", placeholder="v4.0.15.2941")
                title = st.text_input("Title", placeholder="Service release notes")
            with col_b:
                published_at = st.date_input("Published or installed date")
                source = st.text_input("Source URL or note", placeholder="https://github.com/.../releases/tag/...")
                impact_override = st.text_area(
                    "Impact override",
                    placeholder="Optional. Example: Faster searches and fewer failed TV imports.",
                    height=92,
                )
            raw_notes = st.text_area(
                "Release notes / update details",
                placeholder="Paste changelog bullets, Docker image notes, GitHub release notes, or your own install notes.",
                height=220,
            )
            submitted = st.form_submit_button("Add to batch", type="primary")
            if submitted:
                chosen_service = custom_service if service == "Other" else service
                if not raw_notes.strip():
                    st.error("Paste some update notes first.")
                else:
                    add_update(
                        build_update(
                            service=chosen_service,
                            version=version,
                            title=title,
                            source=source,
                            published_at=published_at.isoformat(),
                            raw_notes=raw_notes,
                            impact_override=impact_override,
                        )
                    )
                    st.success("Update added.")

    with output_tab:
        st.subheader("Current Batch")
        if not st.session_state.updates:
            st.info("Add updates from GitHub or paste release notes to build a Discord post.")
        for index, update in enumerate(list(st.session_state.updates)):
            render_update_card(update, index)

        st.divider()
        title = st.text_input("Discord post title", value="Media Stack Update")
        include_sources = st.checkbox("Include source links", value=True)
        message = format_discord_message(st.session_state.updates, title, include_sources)
        chunks = split_for_discord(message)

        st.markdown("**Discord-ready text**")
        if len(chunks) > 1:
            st.warning(f"Discord length guard split this into {len(chunks)} paste chunks.")
        for idx, chunk in enumerate(chunks, start=1):
            st.text_area(
                f"Chunk {idx}",
                value=chunk,
                height=360,
                key=f"discord-chunk-{idx}",
            )
        st.divider()
        st.markdown("**Send to Discord**")
        webhook_default = configured_webhook_url()
        webhook_url = st.text_input(
            "Webhook URL",
            value=webhook_default,
            type="password",
            help="Use DISCORD_WEBHOOK_URL in .env or Streamlit secrets to avoid pasting this every time.",
        )
        dry_run = st.checkbox("Dry run only", value=True)
        col_send, col_validate = st.columns(2)
        with col_validate:
            if st.button("Validate webhook", disabled=not webhook_url):
                try:
                    validate_discord_webhook_url(webhook_url)
                    st.success("Webhook format looks valid.")
                except DiscordWebhookError as exc:
                    st.error(str(exc))
        with col_send:
            if st.button("Send current batch", type="primary", disabled=not st.session_state.updates):
                try:
                    result = send_discord_chunks(webhook_url, chunks, dry_run=dry_run)
                    mode = "validated in dry-run mode" if result.dry_run else "sent"
                    st.success(f"{result.sent} Discord chunk(s) {mode}.")
                except DiscordWebhookError as exc:
                    st.error(str(exc))
        if st.button("Save this batch to history", disabled=not st.session_state.updates):
            save_batch(st.session_state.updates, message)
            st.success("Saved to local history.")

    with history_tab:
        st.subheader("Local History")
        history = load_history()
        if not history:
            st.info("No saved batches yet.")
        for item in history[:10]:
            with st.expander(item.get("created_at", "Saved batch")):
                st.text_area(
                    "Saved Discord message",
                    value=item.get("discord_message", ""),
                    height=260,
                    key=f"history-{item.get('created_at', '')}",
                )


if __name__ == "__main__":
    main()
