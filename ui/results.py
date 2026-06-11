"""Results rendering: dataframe display and CSV export."""

from typing import Dict, List

import pandas as pd
import streamlit as st


def render_results(details: List[Dict]) -> None:
    """Render the results table, CSV download, and caveats."""
    df = pd.DataFrame(details)

    st.success(f"Loaded {len(df)} videos.")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="youtube_data.csv", mime="text/csv")

    st.caption(
        "Note: share_count and remix_count are not available via the public YouTube Data API. "
        "Transcript fetching may be blocked on some networks/hosts (status 'blocked'). "
        "Check transcript_debug_reason for details."
    )
