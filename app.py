"""Streamlit entry point: YouTube Video / Channel Extractor.

Thin orchestration only — parsing, API access, transcripts, and rendering
live in core/, services/, and ui/.

Run with:  streamlit run app.py
"""

import streamlit as st

from core.filters import apply_content_filter
from core.youtube_api import build_youtube_client
from services.extraction import attach_transcripts, collect_video_ids
from ui.components import (
    render_api_key_sidebar,
    render_source_inputs,
    render_transcript_options,
)
from ui.results import render_results


@st.cache_resource(show_spinner=False)
def get_youtube_client(api_key: str):
    """Cache the API client per key so it isn't rebuilt on every rerun."""
    return build_youtube_client(api_key)


def main() -> None:
    st.set_page_config(page_title="YouTube Extractor", layout="wide")
    st.title("YouTube Video / Channel Extractor")

    api_key = render_api_key_sidebar()
    if not api_key:
        st.warning("Enter your YouTube Data API key in the sidebar to continue.")
        st.stop()

    youtube = get_youtube_client(api_key)

    source = render_source_inputs()
    options = render_transcript_options()

    st.markdown("---")
    run = st.button("Fetch data", type="primary")
    if not run:
        return

    with st.spinner("Fetching video metadata..."):
        video_ids = collect_video_ids(youtube, source)
        if video_ids is None:
            st.stop()
        if not video_ids:
            st.warning("No video IDs found.")
            st.stop()

        details = fetch_video_details(youtube, video_ids)
        details = apply_content_filter(details, source.content_filter)

    attach_transcripts(details, options)
    render_results(details)


if __name__ == "__main__":
    main()
