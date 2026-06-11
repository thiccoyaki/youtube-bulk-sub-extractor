"""Orchestration layer: ties core modules together into app-level workflows.

Keeps the Streamlit entry point thin and the core modules UI-agnostic
(except for Streamlit-native caching/progress where it genuinely belongs).
"""

import random
import time
from typing import Dict, List, Optional

import streamlit as st

from core.parsing import extract_video_ids, parse_channel_identifier
from core.transcripts import fetch_transcript_with_retries
from core.youtube_api import (
    fetch_channel_video_ids,
    fetch_video_details,
    resolve_channel_id,
)
from ui.components import INPUT_TYPE_VIDEOS, SourceSelection, TranscriptOptions

CONSECUTIVE_BLOCK_LIMIT = 3


def collect_video_ids(youtube, source: SourceSelection) -> Optional[List[str]]:
    """Resolve the user's input (video list or channel) into video IDs.

    Returns None when a channel could not be resolved (error already shown).
    """
    if source.input_type == INPUT_TYPE_VIDEOS:
        return extract_video_ids(source.video_text)

    ident = parse_channel_identifier(source.channel_text)
    channel_id = resolve_channel_id(youtube, ident)
    if not channel_id:
        st.error(
            "Could not resolve channel ID. Try a UC... channel ID or a more "
            "specific channel URL/handle."
        )
        return None
    return fetch_channel_video_ids(youtube, channel_id, max_results=source.max_channel_results)


def attach_transcripts(details: List[Dict], opts: TranscriptOptions) -> None:
    """Fetch transcripts for each row in-place, with progress, throttle, and cooldowns."""
    if not opts.fetch_transcripts:
        for r in details:
            r["transcript"] = None
            r["transcript_status"] = "skipped"
            r["transcript_debug_reason"] = "Fetch transcripts disabled"
        return

    if opts.min_views_for_transcript:
        st.info(
            f"Fetching transcripts for videos with ≥ {opts.min_views_for_transcript:,} views..."
        )
    else:
        st.info("Fetching transcripts...")
    progress = st.progress(0.0)
    total = len(details)
    consecutive_blocks = 0

    for i, r in enumerate(details, start=1):
        vid = r["video_id"]

        # Skip transcript for videos below the view threshold
        if opts.min_views_for_transcript is not None:
            try:
                views = int(r.get("view_count") or 0)
            except (ValueError, TypeError):
                views = 0
            if views < opts.min_views_for_transcript:
                r["transcript"] = None
                r["transcript_status"] = "skipped_low_views"
                r["transcript_debug_reason"] = (
                    f"view_count {views} < threshold {opts.min_views_for_transcript}"
                )
                progress.progress(i / total)
                continue

        t, status, reason = fetch_transcript_with_retries(
            vid,
            opts.preferred_langs,
            opts.preserve_formatting,
            opts.proxy_http,
            opts.proxy_https,
            max_tries=opts.max_tries,
            base_delay=opts.base_delay,
            max_delay=opts.max_delay,
        )

        r["transcript"] = t
        r["transcript_status"] = status
        r["transcript_debug_reason"] = reason

        # Track consecutive blocks and apply a cooldown if needed
        if status == "blocked":
            consecutive_blocks += 1
        else:
            consecutive_blocks = 0

        if consecutive_blocks >= CONSECUTIVE_BLOCK_LIMIT:
            cooldown = 60 + random.uniform(0, 30)
            st.warning(f"Multiple blocks in a row detected. Cooling down for {cooldown:.0f}s...")
            time.sleep(cooldown)
            consecutive_blocks = 0

        # Base throttle + jitter (helps avoid blocks)
        if opts.base_throttle_ms > 0:
            time.sleep((opts.base_throttle_ms / 1000.0) + random.uniform(0.05, 0.25))

        progress.progress(i / total)
