# SQLite Transcript Database

## Overview

Raw transcript DataFrames produced by `YouTubeTranscriptCollector.collect()` are persisted to a local SQLite database. This avoids re-fetching data from the YouTube API on every run and provides a queryable store of the raw collected data.

## Architecture

```
YouTubeTranscriptCollector.collect()
        │
        ▼
  pandas DataFrame
        │
        └──► TranscriptDatabase.save()  — persist raw rows to SQLite (data/transcripts.db)
```

## Components

### `src/database/transcript_db.py`

`TranscriptDatabase` class — wraps a SQLite database file using Python's stdlib `sqlite3`.

**Initialization:**

```python
db = TranscriptDatabase()
```

Opens (or creates) the database at `settings.transcript_db_path` and creates the `transcripts` table if it does not exist.

**Methods:**

| Method | Description |
|---|---|
| `save(df)` | Insert new rows from `df`, skipping any `video_id` already stored. Returns the count of newly inserted rows. Idempotent. |
| `load()` | Return the full `transcripts` table as a pandas DataFrame. |

## Database Schema

Single table: `transcripts`

| Column | SQLite Type | Description |
|---|---|---|
| `video_id` | `TEXT PRIMARY KEY` | YouTube video ID — unique key |
| `channel` | `TEXT` | Channel display name |
| `channel_id` | `TEXT` | YouTube channel ID (UC...) |
| `title` | `TEXT` | Video title |
| `published_at` | `TEXT` | ISO 8601 publish timestamp |
| `url` | `TEXT` | Full YouTube URL |
| `transcript` | `TEXT` | Full transcript text, or `NULL` if unavailable |
| `transcript_available` | `INTEGER` | `1` if transcript was fetched, `0` otherwise |

`transcript_available` is stored as `INTEGER` (SQLite has no native boolean type) and is cast back to `bool` when loaded via `load()`.

## Usage

```python
from src.database.transcript_db import TranscriptDatabase

db = TranscriptDatabase()

# Save a DataFrame
new_rows = db.save(df)
print(f"{new_rows} new transcript(s) saved.")

# Load all stored transcripts
df = db.load()
print(df.shape)          # (n_videos, 8)
print(df.dtypes)         # transcript_available is bool
```

## Configuration

| Setting | Config key | Default | Description |
|---|---|---|---|
| `transcript_db_path` | `transcript_db_path` | `./data/transcripts.db` | Path to the SQLite database file |

Override via `.env`:

```
TRANSCRIPT_DB_PATH=./data/transcripts.db
```

## Design Decisions

- **Idempotent inserts** — `INSERT OR IGNORE` with `video_id` as `PRIMARY KEY` means re-running the pipeline never creates duplicate rows, without needing a pre-query check.
- **No new dependencies** — `sqlite3` is part of the Python standard library. Nothing is added to `pyproject.toml`.
- **Single store** — The SQLite database holds the full raw DataFrame (including complete transcript text), serving as the sole persistence layer for collected data.
- **`bool` round-trip** — `transcript_available` is cast to `int` on write and back to `bool` on read, preserving the original DataFrame schema for downstream consumers.
