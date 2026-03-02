# YouTube Transcript Module

## Purpose

`src/youtube_transcripts/youtube_transcript.py` is the production module for YouTube transcript collection. It exposes the `YouTubeTranscriptCollector` class, which handles channel resolution, video pagination, transcript fetching, and retry logic.

## How to Use

```python
from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector

collector = YouTubeTranscriptCollector()
df = collector.collect()
```

Configuration is read from `.env` via `config/config.py`. At minimum, set `YOUTUBE_API_KEY`.

## Module-Level Helpers

### `_is_retryable_http_error(e: Exception) -> bool`

Returns `True` if `e` is a `googleapiclient.errors.HttpError` with status code `429`, `500`, or `503`.

### `_is_retryable_transcript_error(e: Exception) -> bool`

Returns `True` if `e` is a `YouTubeRequestFailed` or `RequestBlocked` from `youtube-transcript-api`.

### `_retry_on_error(func, retryable_check, description="API call")`

Calls `func()` with exponential backoff + jitter on retryable errors.

- Retries up to `settings.api_max_retries` times
- Delay formula: `min(base * 2^attempt, max_delay) + uniform(0, delay * 0.5)`
- Raises immediately on non-retryable errors
- Logs a warning on each retry and an error after the final failure

## Class: `YouTubeTranscriptCollector`

### `__init__()`

Builds the YouTube Data API v3 client using `settings.youtube_api_key`. Reads `channels`, `max_videos_per_channel`, and `language` from settings.

### `_resolve_channel_id(channel_input: str) -> dict`

Resolves a channel handle (`@handle`) or channel ID (`UC…`) to its canonical ID and display title.

- Detects format: 24-char strings starting with `"UC"` use `id=`, everything else strips `@` and uses `forHandle=`
- Wraps the API call in `_retry_on_error` with `_is_retryable_http_error`
- Returns `{"channel_id": str, "channel_title": str}`
- Raises `ValueError` if the channel is not found

### `_get_uploads_playlist_id(channel_id: str) -> str`

Retrieves the hidden "uploads" playlist ID for a channel.

- Calls `youtube.channels().list(part="contentDetails")`
- Returns the playlist ID string used as input to `_get_videos_from_playlist`

### `_get_videos_from_playlist(playlist_id: str, max_videos=None) -> list[dict]`

Paginates through a playlist and collects video metadata.

- Fetches up to 50 results per page via `youtube.playlistItems().list()`
- Handles multi-page results via `nextPageToken`
- Respects the optional `max_videos` cap
- Each record: `{"video_id": str, "title": str, "published_at": str}`

### `_get_transcript(video_id: str) -> str | None`

Fetches the full transcript text for a single video.

- Prefers **manually created** transcripts; falls back to **auto-generated** ones via `find_generated_transcript()`
- Uses `_retry_on_error` with `_is_retryable_transcript_error` for the fetch
- Returns `None` on `NoTranscriptFound`, `TranscriptsDisabled`, or any unexpected error
- Logs a warning on unexpected errors

### `collect() -> pd.DataFrame`

Main entry point. Iterates over `self.channels`, resolves each channel, fetches its video list, and calls `_get_transcript()` for each video with a `settings.transcript_delay` sleep between requests. Skips channels that fail resolution and logs an error. Returns a DataFrame on completion.

## Output DataFrame

| Column | Type | Description |
|---|---|---|
| `channel` | str | Channel display name |
| `channel_id` | str | YouTube channel ID (`UC…`) |
| `video_id` | str | YouTube video ID |
| `title` | str | Video title |
| `published_at` | str | ISO 8601 publish timestamp |
| `url` | str | Full `https://www.youtube.com/watch?v=…` URL |
| `transcript` | str \| None | Full transcript text, or `None` if unavailable |
| `transcript_available` | bool | `True` if transcript was successfully fetched |

## Proxy Configuration

`_get_transcript` includes commented-out code for routing requests through a [Webshare](https://www.webshare.io/) rotating proxy:

```python
# from youtube_transcript_api.proxies import WebshareProxyConfig
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=WEB_SHARE_USER,
        proxy_password=WEB_SHARE_PW,
    )
)
```

To enable it, uncomment the import and the block, then set `WEB_SHARE_USERNAME` and `WEB_SHARE_PW` in `.env`.

See [`api-rate-limiting.md`](api-rate-limiting.md) for details on the retry configuration and error handling.
