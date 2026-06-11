# YouTube Video / Channel Extractor

Streamlit app that pulls title, description, transcript, likes, and comments
for a list of YouTube videos or a channel's recent uploads, with robust
transcript fetching (retries, backoff, optional proxy).

## Project structure

```
.
├── app.py                  # Streamlit entry point (thin orchestration only)
├── requirements.txt
├── core/                   # UI-agnostic business logic
│   ├── parsing.py          # URL / video ID / channel identifier parsing
│   ├── youtube_api.py      # YouTube Data API v3 client + metadata fetching
│   ├── transcripts.py      # transcript fetching, caching, retry/backoff
│   ├── filters.py          # Videos vs Shorts content filter
│   └── utils.py            # chunking, dedupe, ISO duration helpers
├── services/
│   └── extraction.py       # workflow orchestration (IDs → metadata → transcripts)
└── ui/
    ├── components.py       # sidebar API key input + option panels
    └── results.py          # results table + CSV export
```

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your YouTube Data API v3 key in the sidebar when the app loads.
The key is kept in the Streamlit session only — no `.env` file or secrets
configuration is required.

## Notes

- `share_count` / `remix_count` are not exposed by the public YouTube Data API.
- Transcript fetching may be blocked on some networks/hosts (status `blocked`);
  configure the optional proxy fields if running on a cloud host.
