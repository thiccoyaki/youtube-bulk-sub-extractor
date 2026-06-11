"""YouTube Data API v3 access: client construction, channel resolution, video metadata."""

from typing import Dict, List, Optional

from googleapiclient.discovery import build

from core.utils import chunked, dedupe_preserve_order, iso_duration_to_seconds


def build_youtube_client(api_key: str):
    """Build a YouTube Data API v3 client from an API key."""
    return build("youtube", "v3", developerKey=api_key)


def resolve_channel_id(youtube, channel_identifier: str) -> Optional[str]:
    """
    Resolve a channel ID from UC..., @handle, or custom text.
    Uses search.list(type=channel) as a pragmatic resolver.
    """
    if channel_identifier.startswith("UC"):
        return channel_identifier

    try:
        q = channel_identifier.lstrip("@")
        resp = (
            youtube.search()
            .list(part="snippet", q=q, type="channel", maxResults=1)
            .execute()
        )
        items = resp.get("items", [])
        if not items:
            return None
        return items[0]["snippet"]["channelId"]
    except Exception:
        return None


def fetch_channel_video_ids(youtube, channel_id: str, max_results: int = 50) -> List[str]:
    """Fetch recent uploads from a channel using search.list(order=date)."""
    video_ids: List[str] = []
    page_token = None

    while len(video_ids) < max_results:
        resp = (
            youtube.search()
            .list(
                part="id",
                channelId=channel_id,
                maxResults=min(50, max_results - len(video_ids)),
                order="date",
                type="video",
                pageToken=page_token,
            )
            .execute()
        )

        for item in resp.get("items", []):
            vid = item["id"].get("videoId")
            if vid:
                video_ids.append(vid)

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return dedupe_preserve_order(video_ids)


def fetch_video_details(youtube, video_ids: List[str]) -> List[Dict]:
    """Batch fetch video details using videos.list (up to 50 IDs per call)."""
    rows: List[Dict] = []
    for batch in chunked(video_ids, 50):
        resp = (
            youtube.videos()
            .list(part="snippet,statistics,contentDetails", id=",".join(batch))
            .execute()
        )

        for item in resp.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            dur_iso = content.get("duration")
            dur_seconds = iso_duration_to_seconds(dur_iso) if dur_iso else None

            rows.append(
                {
                    "video_id": item.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                    "published_at": snippet.get("publishedAt"),
                    "channel_title": snippet.get("channelTitle"),
                    "duration_iso": dur_iso,
                    "duration_seconds": dur_seconds,
                    "like_count": stats.get("likeCount"),
                    "comment_count": stats.get("commentCount"),
                    # Not available in the public API:
                    "share_count": None,
                    "remix_count": None,
                }
            )
    return rows
