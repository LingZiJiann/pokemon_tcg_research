# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- Python 3.10+ - All application code

## Runtime

**Environment:**
- Python interpreter

**Package Manager:**
- pip (via pyproject.toml)
- Lockfile: Not present (no requirements.lock or poetry.lock)

## Frameworks

**Core:**
- None (script-based application without web framework)

**Testing:**
- pytest 7.0+ - Unit and integration testing framework

**Build/Dev:**
- black - Code formatter
- ruff - Linter and code quality tool

## Key Dependencies

**Critical:**
- `google-api-python-client` (via googleapiclient) - YouTube Data API v3 client for channel and video lookup
- `youtube-transcript-api` - Fetches video transcripts from YouTube
- `pandas` - Data manipulation and DataFrame creation
- `pydantic-settings` - Configuration management via environment variables

**Infrastructure:**
- `tqdm` - Progress bar display for transcript collection loops

## Configuration

**Environment:**
- `.env` file contains required API keys and credentials
- Uses `pydantic-settings.BaseSettings` for environment variable validation
- Configuration location: `/config/config.py`

**Required Environment Variables:**
- `web_share_username` - Webshare proxy credentials (optional, commented out)
- `web_share_pw` - Webshare proxy credentials (optional, commented out)
- `youtube_api_key` - YouTube Data API v3 key (required)

**Default Configuration:**
- `channels` - List of YouTube channels to scrape (default: @TwicebakedJake, @okJLUV)
- `max_videos_per_channel` - Maximum videos per channel (default: 1)
- `language` - Transcript language (default: "en")

## Platform Requirements

**Development:**
- Python 3.10 or higher
- macOS (evidenced by Cloud Documents path structure)
- Internet connectivity for YouTube API access

**Production:**
- Python 3.10 or higher
- Valid YouTube Data API v3 credentials
- Internet connectivity for YouTube API and transcript fetching
- No containerization, database, or deployment infrastructure configured

---

*Stack analysis: 2026-02-27*
