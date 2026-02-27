# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Modular Data Collection Pipeline with Composition Pattern

**Key Characteristics:**
- Single-responsibility modules for data collection, configuration, and utilities
- External API client integration (YouTube Data API, YouTube Transcript API)
- Configuration-driven behavior via Pydantic Settings
- Pandas DataFrame output for data analysis
- Centralized logging across all modules

## Layers

**Entry Point Layer:**
- Purpose: Orchestrate the data collection workflow
- Location: `main.py`
- Contains: Main execution function and script entry point
- Depends on: `YouTubeTranscriptCollector` from `src.youtube_transcripts.youtube_transcript`
- Used by: Direct script execution

**Configuration Layer:**
- Purpose: Centralize environment variables and configuration settings
- Location: `config/config.py`
- Contains: Pydantic Settings model with YouTube API credentials and collection parameters
- Depends on: Pydantic Settings library, `.env` file (implicit)
- Used by: `YouTubeTranscriptCollector` initialization

**Data Collection Layer:**
- Purpose: Collect YouTube video transcripts and metadata across multiple channels
- Location: `src/youtube_transcripts/youtube_transcript.py`
- Contains: `YouTubeTranscriptCollector` class with methods for channel resolution, playlist fetching, and transcript retrieval
- Depends on: Google API client, YouTube Transcript API, Pandas, config settings, logger
- Used by: `main.py`

**Utility/Cross-Cutting Concerns Layer:**
- Purpose: Provide shared infrastructure like logging
- Location: `src/utils/logger.py`
- Contains: Logger setup and retrieval functions with file and console handlers
- Depends on: Python standard logging library, pathlib
- Used by: All modules requiring observability

## Data Flow

**YouTube Transcript Collection Flow:**

1. `main.py` instantiates `YouTubeTranscriptCollector` with configuration from `config.settings`
2. `YouTubeTranscriptCollector.__init__()` initializes YouTube API client and loads configuration parameters
3. `collect()` iterates through configured channels:
   - Calls `_resolve_channel_id()` to convert channel handle/ID to channel ID
   - Calls `_get_uploads_playlist_id()` to retrieve the channel's uploads playlist
   - Calls `_get_videos_from_playlist()` to fetch video metadata (with pagination support)
   - For each video, calls `_get_transcript()` to retrieve transcript text
4. Transcripts are accumulated in a list of dictionaries
5. List is converted to Pandas DataFrame with columns: channel, channel_id, video_id, title, published_at, url, transcript, transcript_available
6. DataFrame is logged with summary statistics and returned to caller

**State Management:**
- All state is local to `YouTubeTranscriptCollector` instance variables set at initialization
- No persistent state across function calls (no database, no caching)
- Configuration loaded once at initialization from environment
- Rate limiting implemented via 2-second sleep between transcript fetches

## Key Abstractions

**YouTubeTranscriptCollector:**
- Purpose: Encapsulate all YouTube data collection logic and API interactions
- Examples: `src/youtube_transcripts/youtube_transcript.py`
- Pattern: Composition pattern - aggregates YouTube API client and configuration. Helper methods extract specific concerns (channel resolution, playlist retrieval, transcript fetching)

**Settings:**
- Purpose: Centralize configuration and environment variable management
- Examples: `config/config.py`
- Pattern: Pydantic Settings model with environment file support. Single instance `settings` is module-level singleton

**Logger:**
- Purpose: Provide consistent logging across the application
- Examples: `src/utils/logger.py`
- Pattern: Factory pattern with `setup_logger()` and `get_logger()` functions. Lazy initialization - loggers are created on first access

## Entry Points

**main.py:**
- Location: `main.py`
- Triggers: Script execution via `python main.py` or import
- Responsibilities:
  - Instantiate `YouTubeTranscriptCollector`
  - Call `collect()` method
  - Print resulting DataFrame

## Error Handling

**Strategy:** Graceful degradation with logging

**Patterns:**
- Channel-level errors: Try-except wrapper around channel processing (`collect()` method lines 176-188). On error, logs error and continues with next channel
- Transcript-level errors: Try-except in `_get_transcript()` (lines 134-150) catches `NoTranscriptFound`, `TranscriptsDisabled`, and generic exceptions. Returns None on failure
- Transcript unavailability: Gracefully handled - transcript column contains None value and `transcript_available` boolean flag indicates success
- API errors: Caught as generic exceptions and logged with warning level

## Cross-Cutting Concerns

**Logging:**
- Implementation: Python `logging` module via `src/utils/logger.py`
- Strategy: Every major operation logged (channel processing start, channel resolution, video discovery, transcript completion)
- Log levels: INFO for normal flow, WARNING for recoverable errors, ERROR for channel-level failures
- Output: Dual handlers - file (detailed format with function name and line number) and console (simplified format)

**Configuration:**
- Implementation: Pydantic BaseSettings in `config/config.py`
- Strategy: Environment variables loaded from `.env` file at import time
- Required vars: `youtube_api_key`, `web_share_username`, `web_share_pw`
- Optional vars: `channels` (list, default two channels), `max_videos_per_channel` (int, default 1), `language` (str, default "en")

**API Rate Limiting:**
- Implementation: 2-second sleep after each transcript fetch (line 202 in `youtube_transcript.py`)
- Strategy: Deliberate delay to respect API rate limits and avoid overwhelming target services

**Data Validation:**
- Channel input validation: Checks for channel ID format (24 chars starting with "UC") vs handle format (starts with "@")
- API response validation: Checks for empty items list when resolving channels

---

*Architecture analysis: 2026-02-27*
