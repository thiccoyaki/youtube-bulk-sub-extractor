"""Filtering of video rows by content type (videos vs. Shorts)."""

from typing import Dict, List

FILTER_ALL = "All"
FILTER_VIDEOS_ONLY = "Videos only"
FILTER_SHORTS_ONLY = "Shorts only"

CONTENT_FILTERS = [FILTER_ALL, FILTER_VIDEOS_ONLY, FILTER_SHORTS_ONLY]

SHORTS_MAX_DURATION_SECONDS = 60


def apply_content_filter(rows: List[Dict], mode: str) -> List[Dict]:
    """
    mode: All | Videos only | Shorts only
    Shorts heuristic: duration_seconds <= 60
    """
    if mode == FILTER_SHORTS_ONLY:
        return [
            r
            for r in rows
            if r.get("duration_seconds") is not None
            and r["duration_seconds"] <= SHORTS_MAX_DURATION_SECONDS
        ]
    if mode == FILTER_VIDEOS_ONLY:
        return [
            r
            for r in rows
            if r.get("duration_seconds") is None
            or r["duration_seconds"] > SHORTS_MAX_DURATION_SECONDS
        ]
    return rows
