"""Transcript fetching via youtube-transcript-api, with version-safe exceptions,
optional proxy support, caching, and randomized exponential backoff on blocks."""

import random
import time
from typing import List, Optional, Tuple

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# Version-safe exception imports (library changes across releases)
try:
    from youtube_transcript_api._errors import RequestBlocked
except ImportError:

    class RequestBlocked(Exception):
        pass


try:
    from youtube_transcript_api._errors import IpBlocked
except ImportError:

    class IpBlocked(Exception):
        pass


# Optional proxy support
try:
    from youtube_transcript_api.proxies import GenericProxyConfig
except Exception:
    GenericProxyConfig = None  # proxy support unavailable if import fails

DEFAULT_LANGUAGES = ("en", "en-US", "en-GB")


def init_transcript_client(
    proxy_http: Optional[str], proxy_https: Optional[str]
) -> YouTubeTranscriptApi:
    """Initialize YouTubeTranscriptApi with optional proxy support."""
    if (proxy_http or proxy_https) and GenericProxyConfig is not None:
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=proxy_http,
                https_url=proxy_https,
            )
        )
    return YouTubeTranscriptApi()


def get_transcript_text(
    ytt_api: YouTubeTranscriptApi,
    video_id: str,
    languages: Optional[List[str]] = None,
    preserve_formatting: bool = False,
) -> Tuple[Optional[str], str, str]:
    """
    Fetch a transcript using the instance API: ytt_api.fetch(video_id, ...).
    Returns (transcript_text, status, debug_reason).

    status: ok | disabled | missing | unavailable | blocked | error
    """
    languages = languages or list(DEFAULT_LANGUAGES)

    try:
        fetched = ytt_api.fetch(
            video_id,
            languages=languages,
            preserve_formatting=preserve_formatting,
        )
        text = " ".join(s.text for s in fetched.snippets).strip()
        if not text:
            return None, "missing", "Empty transcript"
        return text, "ok", f"lang={fetched.language_code}, generated={fetched.is_generated}"

    except (RequestBlocked, IpBlocked) as e:
        return None, "blocked", type(e).__name__

    except TranscriptsDisabled as e:
        return None, "disabled", type(e).__name__

    except NoTranscriptFound as e:
        return None, "missing", type(e).__name__

    except VideoUnavailable as e:
        return None, "unavailable", type(e).__name__

    except CouldNotRetrieveTranscript as e:
        # Frequently indicates blocked/rate-limited or YouTube endpoint changes
        return None, "blocked", f"CouldNotRetrieveTranscript:{type(e).__name__}"

    except Exception as e:
        return None, "error", f"{type(e).__name__}: {e}"


@st.cache_data(ttl=3600, show_spinner=False)
def cached_transcript(
    video_id: str,
    languages_tuple: Tuple[str, ...],
    preserve_formatting: bool,
    proxy_http: Optional[str],
    proxy_https: Optional[str],
) -> Tuple[Optional[str], str, str]:
    """Cached transcript fetch. Cache key includes proxy settings."""
    ytt_api = init_transcript_client(proxy_http, proxy_https)
    return get_transcript_text(
        ytt_api,
        video_id,
        languages=list(languages_tuple),
        preserve_formatting=preserve_formatting,
    )


def fetch_transcript_with_retries(
    video_id: str,
    preferred_langs: Tuple[str, ...],
    preserve_formatting: bool,
    proxy_http: Optional[str],
    proxy_https: Optional[str],
    max_tries: int = 4,
    base_delay: float = 1.5,
    max_delay: float = 30.0,
) -> Tuple[Optional[str], str, str]:
    """Randomized exponential backoff retries ONLY for 'blocked' transcripts."""
    last_reason = "blocked"
    for attempt in range(1, max_tries + 1):
        t, status, reason = cached_transcript(
            video_id,
            preferred_langs,
            preserve_formatting,
            proxy_http,
            proxy_https,
        )

        if status != "blocked":
            return t, status, reason

        last_reason = reason
        exp_delay = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0.5, 2.0)
        sleep_time = min(exp_delay * jitter, max_delay)

        print(f"[{video_id}] Blocked. Retry {attempt}/{max_tries} in {sleep_time:.2f}s ({reason})")
        time.sleep(sleep_time)

    return None, "blocked", f"{last_reason} (after {max_tries} retries)"
