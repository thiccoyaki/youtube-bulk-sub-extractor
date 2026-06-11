"""Small generic helpers shared across the app."""

from typing import Iterator, List, Optional

import isodate


def chunked(items: List[str], n: int) -> Iterator[List[str]]:
    """Yield successive n-sized chunks from a list."""
    for i in range(0, len(items), n):
        yield items[i : i + n]


def dedupe_preserve_order(items: List[str]) -> List[str]:
    """Remove duplicates while preserving original order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def iso_duration_to_seconds(iso_dur: str) -> Optional[int]:
    """Convert an ISO 8601 duration string (e.g. PT1M30S) to seconds."""
    try:
        td = isodate.parse_duration(iso_dur)
        return int(td.total_seconds())
    except Exception:
        return None
