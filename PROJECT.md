# Pokemon TCG Research

Sentiment and market analysis on Pokemon TCG based on influential YouTubers.

## Goal

Collect YouTube transcripts from Pokemon TCG content creators, summarize and verify them with AI, and persist insights to SQLite — tracking card price trends, meta shifts, and community sentiment.

## Stack

| Layer | Technology |
|---|---|
| Language | Python ≥ 3.10 |
| Config | `pydantic-settings` + `.env` |
| YouTube data | YouTube Data API v3 + `youtube-transcript-api` |
| Summarization | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) + Ollama fallback (`gpt-oss:20b`) |
| Verification | Tavily search API (general market + eBay last-sold) |
| Data wrangling | pandas |

## Project Structure

```
pokemon_tcg_research/
├── main.py                         # Entry point: collect → save → summarize → verify
├── youtube_transcript.ipynb        # Prototype notebook: fetch & inspect transcripts interactively
├── config/
│   └── config.py                   # Pydantic Settings (all config + .env overrides)
├── src/
│   ├── youtube_transcripts/
│   │   └── youtube_transcript.py   # YouTubeTranscriptCollector — fetch & retry
│   ├── database/
│   │   └── transcript_db.py        # TranscriptDatabase — persist & load transcripts, summaries, verifications (SQLite)
│   ├── summarizer/
│   │   └── summarizer.py           # TranscriptSummarizer — Claude Haiku + Ollama fallback
│   ├── verifier/
│   │   └── verifier.py             # TranscriptVerifier — Tavily + eBay verification + Claude refinement (feedback loop)
│   └── utils/
│       └── logger.py               # Shared logger
├── data/                           # Persistent data files (gitignored)
│   └── transcripts.db              # SQLite database (transcripts + summaries + verifications tables)
├── logs/                           # Per-run log files
├── docs/                           # Feature documentation (auto-loaded by PROJECT.md)
└── pyproject.toml
```

## Pipeline

```
YouTube Data API
       │
       ▼
YouTubeTranscriptCollector.collect()   — fetches video list + transcripts per channel
       │
       ▼
pandas DataFrame
       │
       └──► TranscriptDatabase.save()          — raw transcripts → SQLite (transcripts table)
                   │
                   ▼
            TranscriptSummarizer.run()          — Claude Haiku (→ Ollama fallback) → SQLite (summaries table)
                   │
                   ▼
            TranscriptVerifier.run()            — Tavily + eBay price search → SQLite (verifications table)
                   │                              Claude re-prompted with verification → SQLite (summaries.refined_summary)
                   ▼
            [feedback loop complete]
```

## Key Configuration (`.env` overrides)

| Setting | Default | Purpose |
|---|---|---|
| `YOUTUBE_API_KEY` | — | YouTube Data API key (required) |
| `CHANNELS` | `["@TwicebakedJake", "@okJLUV"]` | Target YouTube channels |
| `MAX_VIDEOS_PER_CHANNEL` | `1` | Video fetch limit per channel |
| `TRANSCRIPT_DELAY` | `2.0` | Seconds between transcript fetches |
| `API_MAX_RETRIES` | `3` | Retry attempts for transient errors |
| `API_RETRY_BASE_DELAY` | `2.0` | Exponential backoff base (seconds) |
| `API_RETRY_MAX_DELAY` | `60.0` | Backoff cap (seconds) |
| `TRANSCRIPT_DB_PATH` | `./data/transcripts.db` | SQLite transcript database path |
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude summarization (optional — falls back to Ollama) |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | Claude model for summarization |
| `OLLAMA_MODEL` | `gpt-oss:20b` | Ollama model for summarization fallback |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `SUMMARY_MAX_TOKENS` | `1024` | Max tokens for generated summaries |
| `TAVILY_API_KEY` | — | Tavily API key for verification searches (optional — skips verification if absent) |
| `MAX_CARDS_PER_VERIFICATION` | `5` | Max cards to search per video (caps Tavily API calls) |
| `VERIFICATION_SEARCH_DEPTH` | `basic` | Tavily search depth: `basic` or `advanced` |

## Features Completed

- [x] YouTube transcript collection with channel-based pagination
- [x] API rate limiting: configurable delay between transcript fetches
- [x] Retry logic: exponential backoff + jitter for transient HTTP/transcript errors
- [x] SQLite transcript database: raw transcript storage with idempotent inserts
- [x] AI summarization agent: Claude Haiku primary with Ollama fallback, summaries persisted to SQLite
- [x] Verification agent: Tavily search (general market + eBay last-sold) cross-checks price claims in each summary
- [x] Feedback loop: verified price data fed back to Claude to produce a refined summary, stored alongside the original

## Documentation

Feature docs live in [`docs/`](docs/):

- [`youtube-transcript.md`](docs/youtube-transcript.md) — production module reference: `YouTubeTranscriptCollector` class, methods, output schema, retry helpers, proxy config
- [`api-rate-limiting.md`](docs/api-rate-limiting.md) — rate limiting, retry logic, error handling table
- [`sqlite-transcript-database.md`](docs/sqlite-transcript-database.md) — `TranscriptDatabase` class, schema, idempotent save/load, design decisions
- [`ai-summarization.md`](docs/ai-summarization.md) — `TranscriptSummarizer` class, Claude + Ollama fallback, summaries schema, prompt template, idempotency
- [`verification-and-feedback-loop.md`](docs/verification-and-feedback-loop.md) — `TranscriptVerifier` class, Tavily + eBay search, verifications schema, refined summary feedback loop, configuration
