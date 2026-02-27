# API Rate Limiting & Retry Logic

## Problem

The YouTube transcript collector had no rate limiting beyond a hard-coded `time.sleep(2)` between transcript fetches. There was zero retry logic — any transient API error (429, 503) would cause an entire channel to be skipped or a transcript to be silently lost.

## What Changed

### `config/config.py`

Added 4 configurable rate limiting settings with sensible defaults:

| Setting | Default | Description |
|---|---|---|
| `transcript_delay` | `1.5` | Seconds between transcript fetches |
| `api_max_retries` | `3` | Max retry attempts for retryable errors |
| `api_retry_base_delay` | `2.0` | Base delay (seconds) for exponential backoff |
| `api_retry_max_delay` | `60.0` | Cap on backoff delay (seconds) |

All settings are overridable via environment variables in `.env`:

```
TRANSCRIPT_DELAY=3.0
API_MAX_RETRIES=5
API_RETRY_BASE_DELAY=2.0
API_RETRY_MAX_DELAY=60.0
```

### `src/youtube_transcripts/youtube_transcript.py`

**New module-level functions:**

- `_retry_on_error(func, retryable_check, description)` — Calls `func()` with exponential backoff + random jitter on retryable errors. Backoff formula: `min(base_delay * 2^attempt, max_delay) + random(0, delay * 0.5)`.

- `_is_retryable_http_error(e)` — Returns `True` for `HttpError` with status 429, 500, or 503. Returns `False` for 403 (daily quota exhausted — retrying won't help).

- `_is_retryable_transcript_error(e)` — Returns `True` for `YouTubeRequestFailed` and `RequestBlocked` from the youtube-transcript-api.

**Updated methods:**

All 5 API call sites are now wrapped with `_retry_on_error`:

| Method | API | Retry check |
|---|---|---|
| `_resolve_channel_id` (2 call sites) | YouTube Data API | `_is_retryable_http_error` |
| `_get_uploads_playlist_id` | YouTube Data API | `_is_retryable_http_error` |
| `_get_videos_from_playlist` (pagination loop) | YouTube Data API | `_is_retryable_http_error` |
| `_get_transcript` | youtube-transcript-api | `_is_retryable_transcript_error` |

The hard-coded `time.sleep(2)` in `collect()` was replaced with `time.sleep(settings.transcript_delay)`.

## Error Handling Behavior

| Error | API | Retried? | Outcome if exhausted |
|---|---|---|---|
| `HttpError` 429/500/503 | YouTube Data API | Yes (3x) | Channel skipped |
| `HttpError` 403 (quota) | YouTube Data API | No | Channel skipped immediately |
| `YouTubeRequestFailed` | youtube-transcript-api | Yes (3x) | Transcript = None |
| `RequestBlocked` | youtube-transcript-api | Yes (3x) | Transcript = None |
| `NoTranscriptFound` | youtube-transcript-api | No | Transcript = None |
| `TranscriptsDisabled` | youtube-transcript-api | No | Transcript = None |

## Design Decisions

- **No new files or dependencies** — the retry helper lives in `youtube_transcript.py` and uses only `random` (stdlib) and `HttpError` (already installed via google-api-python-client).
- **Jitter prevents thundering herd** — random delay between 0-50% of base delay spreads out retries.
- **403 is not retried** — YouTube Data API quota resets daily; retrying wastes time.
- **Each pagination page is individually retried** — a failure on page 3 doesn't restart from page 1.
- **`YouTubeTranscriptApi()` is re-instantiated on each retry** — ensures no stale state.
