# External Integrations

**Analysis Date:** 2026-02-27

## APIs & External Services

**YouTube:**
- YouTube Data API v3 - Fetches channel information, video playlists, and video metadata
  - SDK/Client: `google-api-python-client` (googleapiclient.discovery.build)
  - Auth: `youtube_api_key` environment variable
  - Usage: `src/youtube_transcripts/youtube_transcript.py` - YouTubeTranscriptCollector class
  - Endpoints used:
    - `youtube.channels().list()` - Resolve channel handles to IDs and get channel details
    - `youtube.playlistItems().list()` - Fetch videos from uploads playlist with pagination

- YouTube Transcript API - Extracts closed captions and auto-generated transcripts
  - SDK/Client: `youtube-transcript-api` (YouTubeTranscriptApi)
  - Auth: No authentication required (public API)
  - Usage: `src/youtube_transcripts/youtube_transcript.py` - _get_transcript() method
  - Handles manual transcripts, generated transcripts, language fallback, and disabled transcripts

**Webshare Proxy (Optional/Commented Out):**
- Service: Webshare proxy for request forwarding
- Auth: `web_share_username`, `web_share_pw` environment variables
- Status: Currently disabled (import commented out at line 10 of youtube_transcript.py)
- Reason: Activated if YouTube API blocks requests

## Data Storage

**Databases:**
- None - Application uses no persistent database

**File Storage:**
- Local filesystem only
  - Logs directory: `logs/` - Application logs stored with timestamp
  - Config directory: `config/` - Configuration files
  - No cloud storage integration

**Caching:**
- None - No caching layer implemented

## Authentication & Identity

**Auth Provider:**
- Custom: API key-based authentication
  - YouTube API Key stored in `.env` as `youtube_api_key`
  - Webshare proxy credentials stored in `.env` as `web_share_username` and `web_share_pw`
  - No OAuth, no user authentication system

## Monitoring & Observability

**Error Tracking:**
- None - No error tracking service integrated

**Logs:**
- Local file-based logging via Python logging module
  - Configuration: `src/utils/logger.py`
  - Log files: `logs/youtube_transcript_YYYYMMDD.log`
  - Format: Detailed format with function name and line numbers for file logs; simpler format for console
  - Levels: INFO (default), configurable to DEBUG, WARNING, ERROR, CRITICAL
  - Two handlers: File handler (detailed) and console handler (optional)

## CI/CD & Deployment

**Hosting:**
- None - Local script execution only
- No deployment infrastructure configured

**CI Pipeline:**
- None - No CI/CD automation configured

## Environment Configuration

**Required env vars:**
- `youtube_api_key` - YouTube Data API v3 authentication key
- `web_share_username` - Webshare proxy username (optional, currently unused)
- `web_share_pw` - Webshare proxy password (optional, currently unused)

**Optional env vars:**
- Channels and max_videos_per_channel have defaults defined in `config/config.py`
- Language defaults to English ("en")

**Secrets location:**
- `.env` file in project root (noted in .gitignore)
- Environment variables loaded via pydantic-settings BaseSettings
- Path: `/config/config.py` - Settings class loads from `.env`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Rate Limiting & Quotas

**YouTube API v3:**
- Rate limiting: YouTube API has quota limits (default 10,000 units/day)
- Throttling: 2-second sleep between transcript requests in `collect()` method (line 202)
- Pagination: Automatic handling for playlist items (50 items per request)

## API Request Patterns

**Request Flow:**
1. Initialize YouTube API client with `google-api-python-client`
2. Resolve channel handle (e.g., @TwicebakedJake) to channel ID via `channels().list(forHandle=...)`
3. Fetch uploads playlist ID via `channels().list(part='contentDetails')`
4. Paginate through playlist items via `playlistItems().list()` with nextPageToken
5. For each video, fetch transcript via `YouTubeTranscriptApi`
6. Handle fallbacks: manual transcripts → generated transcripts → None if unavailable
7. Return pandas DataFrame with collected data

---

*Integration audit: 2026-02-27*
