"""Parsing of user-supplied YouTube URLs, video IDs, and channel identifiers."""

import re
from typing import List

from core.utils import dedupe_preserve_order

YOUTUBE_VIDEO_ID_RE = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|\/|$)")
YOUTUBE_SHORTS_RE = re.compile(r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})")
RAW_VIDEO_ID_RE = re.compile(r"[0-9A-Za-z_-]{11}")
CHANNEL_URL_RE = re.compile(r"youtube\.com\/channel\/(UC[0-9A-Za-z_-]+)")
HANDLE_URL_RE = re.compile(r"youtube\.com\/@([0-9A-Za-z_.-]+)")


def extract_video_ids(text: str) -> List[str]:
    """Accept multiple lines of URLs/IDs and return unique 11-char video IDs."""
    ids: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # The line itself is an 11-char ID
        if RAW_VIDEO_ID_RE.fullmatch(line):
            ids.append(line)
            continue

        m = YOUTUBE_SHORTS_RE.search(line)
        if m:
            ids.append(m.group(1))
            continue

        m = YOUTUBE_VIDEO_ID_RE.search(line)
        if m:
            ids.append(m.group(1))
            continue

    return dedupe_preserve_order(ids)


def parse_channel_identifier(channel_input: str) -> str:
    """
    Accepts channel URL, handle URL, @handle, or raw channel ID.
    Returns an identifier that can be resolved into a channelId.
    """
    s = channel_input.strip()

    # Raw channel ID (starts with UC...)
    if s.startswith("UC") and len(s) >= 20:
        return s

    # Handle like @something
    if s.startswith("@"):
        return s

    m = CHANNEL_URL_RE.search(s)
    if m:
        return m.group(1)

    m = HANDLE_URL_RE.search(s)
    if m:
        return "@" + m.group(1)

    return s
