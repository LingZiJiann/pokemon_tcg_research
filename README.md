# Pokemon TCG Research

Sentiment and market analysis on Pokemon TCG based on influential YouTubers.

## Motivation

Pokemon TCG YouTube influencers regularly make bold claims about card prices and market trends — but how do you know what's actually worth acting on? This project was born from three needs:

1. **Understand current market trends** — aggregate what influential YouTubers are saying to get a pulse on the Pokemon TCG market without watching hours of content.
2. **Verify their claims** — cross-check price predictions and "buy now" calls against real market data (eBay last-sold prices, general market sources) so hype doesn't drive bad decisions.
3. **Get actionable insights** — when claims hold up, surface concrete buy/skip recommendations ranked by confidence so you can act quickly on genuine opportunities.

## Features

- **YouTube transcript collection** — channel-based video discovery with configurable pagination and rate limiting
- **AI summarization** — Claude Haiku primary with Ollama fallback for card mentions, price claims, and meta shifts
- **Market verification** — Tavily search (general market + eBay last-sold) cross-checks price claims
- **Buy recommendations** — verified prices fed back to Claude for per-card buy/skip verdicts and ranked top picks
- **SQLite persistence** — idempotent storage for transcripts, summaries, and verifications
- **Resilient API calls** — exponential backoff + jitter retry logic for transient errors

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
                   │                              Claude generates buy recommendations → SQLite (summaries.buy_recommendations)
                   ▼
            [feedback loop complete]
```

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python >= 3.10 |
| Config | `pydantic-settings` + `.env` |
| YouTube data | YouTube Data API v3 + `youtube-transcript-api` |
| Summarization | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) + Ollama fallback |
| Verification | Tavily search API (general market + eBay last-sold) |
| Data wrangling | pandas |

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [YouTube Data API](https://console.cloud.google.com/) key (required)
- An [Anthropic API](https://console.anthropic.com/) key (optional — falls back to Ollama)
- A [Tavily API](https://tavily.com/) key (optional — skips verification if absent)

### Installation

```bash
git clone https://github.com/your-username/pokemon_tcg_research.git
cd pokemon_tcg_research
uv sync
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
YOUTUBE_API_KEY=your_youtube_api_key

# Optional (falls back to Ollama if absent)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional (skips verification if absent)
TAVILY_API_KEY=your_tavily_api_key
```

## Usage

```bash
python main.py
```

This runs the full pipeline: collect transcripts, save to SQLite, summarize with AI, verify prices, and generate buy recommendations.

## Configuration

All settings are configurable via `.env` overrides:

| Setting | Default | Purpose |
|---|---|---|
| `YOUTUBE_API_KEY` | — | YouTube Data API key (required) |
| `CHANNELS` | `["@TwicebakedJake", "@okJLUV"]` | Target YouTube channels |
| `MAX_VIDEOS_PER_CHANNEL` | `1` | Video fetch limit per channel |
| `TRANSCRIPT_DELAY` | `2.0` | Seconds between transcript fetches |
| `API_MAX_RETRIES` | `3` | Retry attempts for transient errors |
| `API_RETRY_BASE_DELAY` | `2.0` | Exponential backoff base (seconds) |
| `API_RETRY_MAX_DELAY` | `60.0` | Backoff cap (seconds) |
| `TRANSCRIPT_DB_PATH` | `./data/transcripts.db` | SQLite database path |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (optional) |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | Claude model for summarization |
| `OLLAMA_MODEL` | `gpt-oss:20b` | Ollama fallback model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `SUMMARY_MAX_TOKENS` | `1024` | Max tokens for summaries |
| `TAVILY_API_KEY` | — | Tavily API key (optional) |
| `MAX_CARDS_PER_VERIFICATION` | `5` | Max cards to verify per video |
| `VERIFICATION_SEARCH_DEPTH` | `basic` | Tavily search depth (`basic` / `advanced`) |

## Project Structure

```
pokemon_tcg_research/
├── main.py                         # Entry point: collect → save → summarize → verify
├── config/
│   └── config.py                   # Pydantic Settings (all config + .env overrides)
├── src/
│   ├── youtube_transcripts/
│   │   └── youtube_transcript.py   # YouTubeTranscriptCollector — fetch & retry
│   ├── database/
│   │   └── transcript_db.py        # TranscriptDatabase — SQLite persistence
│   ├── summarizer/
│   │   └── summarizer.py           # TranscriptSummarizer — Claude + Ollama fallback
│   ├── verifier/
│   │   └── verifier.py             # TranscriptVerifier — Tavily + buy recommendations
│   └── utils/
│       └── logger.py               # Shared logger
├── data/                           # SQLite database (gitignored)
├── logs/                           # Per-run log files (gitignored)
├── docs/                           # Feature documentation
└── notebooks/                      # Jupyter notebooks
```

## Documentation

Detailed feature docs live in [`docs/`](docs/):

- [YouTube Transcript Collection](docs/youtube-transcript.md) — `YouTubeTranscriptCollector` class, methods, output schema, proxy config
- [API Rate Limiting](docs/api-rate-limiting.md) — rate limiting, retry logic, error handling
- [SQLite Database](docs/sqlite-transcript-database.md) — `TranscriptDatabase` class, schema, idempotent operations
- [AI Summarization](docs/ai-summarization.md) — `TranscriptSummarizer` class, Claude + Ollama fallback, prompt template
- [Verification & Feedback Loop](docs/verification-and-feedback-loop.md) — `TranscriptVerifier` class, Tavily search, buy recommendations
