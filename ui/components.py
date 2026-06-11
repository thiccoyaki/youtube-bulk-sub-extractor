"""Streamlit UI components: API key sidebar, source inputs, and option panels."""

from dataclasses import dataclass
from typing import Optional, Tuple

import streamlit as st

from core.filters import CONTENT_FILTERS

INPUT_TYPE_VIDEOS = "Multiple video links / IDs"
INPUT_TYPE_CHANNEL = "Channel"


@dataclass
class TranscriptOptions:
    fetch_transcripts: bool
    preserve_formatting: bool
    base_throttle_ms: int
    preferred_langs: Tuple[str, ...]
    max_tries: int
    base_delay: float
    max_delay: float
    proxy_http: Optional[str]
    proxy_https: Optional[str]
    min_views_for_transcript: Optional[int]


@dataclass
class SourceSelection:
    input_type: str
    content_filter: str
    max_channel_results: int
    video_text: str
    channel_text: str


def render_api_key_sidebar() -> Optional[str]:
    """Render the API key input in the sidebar. Returns the key or None."""
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input(
            "YouTube Data API key",
            type="password",
            help="Create one in Google Cloud Console → APIs & Services → Credentials. "
            "The key stays in this session only and is never stored.",
        ).strip()
        if not api_key:
            st.info("Enter your YouTube Data API v3 key to get started.")
    return api_key or None


def render_source_inputs() -> SourceSelection:
    """Render input-type selection, content filter, and source text inputs."""
    col1, col2 = st.columns(2)
    with col1:
        input_type = st.radio(
            "Input type", [INPUT_TYPE_VIDEOS, INPUT_TYPE_CHANNEL], horizontal=True
        )
    with col2:
        content_filter = st.radio("Content filter", CONTENT_FILTERS, horizontal=True)

    max_channel_results = st.slider(
        "Max videos to fetch (channel mode)", 5, 200, 50, step=5
    )

    video_text = ""
    channel_text = ""

    if input_type == INPUT_TYPE_VIDEOS:
        video_text = st.text_area(
            "Paste YouTube video URLs or IDs (one per line)",
            height=200,
            placeholder=(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
                "https://youtube.com/shorts/XXXXXXXXXXX\n"
                "XXXXXXXXXXX"
            ),
        )
    else:
        channel_text = st.text_input(
            "Channel URL, handle (@...), or channel ID (UC...)",
            placeholder="https://www.youtube.com/@channelhandle",
        )

    return SourceSelection(
        input_type=input_type,
        content_filter=content_filter,
        max_channel_results=max_channel_results,
        video_text=video_text,
        channel_text=channel_text,
    )


def render_transcript_options() -> TranscriptOptions:
    """Render transcript, retry, and proxy option panels."""
    st.markdown("### Transcript options")
    opt_col1, opt_col2, opt_col3 = st.columns(3)
    with opt_col1:
        fetch_transcripts = st.checkbox("Fetch transcripts (slower)", value=True)
    with opt_col2:
        preserve_formatting = st.checkbox("Preserve formatting (<i>, <b>, etc.)", value=False)
    with opt_col3:
        base_throttle_ms = st.number_input(
            "Base throttle per transcript (ms)",
            min_value=0,
            max_value=3000,
            value=150,
            step=50,
            help="A small base delay helps avoid blocks; random jitter is added automatically.",
        )

    languages_input = st.text_input(
        "Preferred transcript languages (comma-separated codes, in priority order)",
        value="en,en-US,en-GB",
        help="Example: de,en  → try German then English",
    )
    preferred_langs = tuple(
        [x.strip() for x in languages_input.split(",") if x.strip()] or ["en"]
    )

    min_views_raw = st.number_input(
        "Only fetch captions for videos above X views (0 = all)",
        min_value=0,
        max_value=100_000_000,
        value=0,
        step=1000,
        help="Set a threshold to skip transcript fetching for low-view videos. "
        "Metadata is still fetched for every video.",
    )
    min_views_for_transcript: Optional[int] = int(min_views_raw) if min_views_raw > 0 else None

    st.markdown("### Retry policy (when blocked)")
    retry_col1, retry_col2, retry_col3 = st.columns(3)
    with retry_col1:
        max_tries = st.number_input("Max retries", min_value=0, max_value=10, value=4, step=1)
    with retry_col2:
        base_delay = st.number_input(
            "Base delay (sec)", min_value=0.0, max_value=60.0, value=1.5, step=0.5
        )
    with retry_col3:
        max_delay = st.number_input(
            "Max delay (sec)", min_value=1.0, max_value=300.0, value=30.0, step=1.0
        )

    st.markdown("### Optional proxy (helps if YouTube blocks your IP on cloud hosts)")
    proxy_cols = st.columns(2)
    with proxy_cols[0]:
        proxy_http = (
            st.text_input("PROXY_HTTP", placeholder="http://user:pass@host:port").strip()
            or None
        )
    with proxy_cols[1]:
        proxy_https = (
            st.text_input("PROXY_HTTPS", placeholder="https://user:pass@host:port").strip()
            or None
        )

    return TranscriptOptions(
        fetch_transcripts=fetch_transcripts,
        preserve_formatting=preserve_formatting,
        base_throttle_ms=int(base_throttle_ms),
        preferred_langs=preferred_langs,
        max_tries=int(max_tries),
        base_delay=float(base_delay),
        max_delay=float(max_delay),
        proxy_http=proxy_http,
        proxy_https=proxy_https,
        min_views_for_transcript=min_views_for_transcript,
    )
