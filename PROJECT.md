# Pokemon TCG Research

Sentiment and market analysis on Pokemon TCG based on influential YouTubers.

## Goal

Collect YouTube transcripts from Pokemon TCG content creators, embed them into a local vector database, and enable semantic search/RAG queries over the collected content — e.g. tracking card price trends, meta shifts, and community sentiment.

## Stack

| Layer | Technology |
|---|---|
| Language | Python ≥ 3.10 |
| Config | `pydantic-settings` + `.env` |
| YouTube data | YouTube Data API v3 + `youtube-transcript-api` |
| Embedding model | `all-MiniLM-L6-v2` (local, via `sentence-transformers`) |
| Vector database | ChromaDB (persistent, on-disk) |
| Data wrangling | pandas |

## Project Structure

```
pokemon_tcg_research/
├── main.py                         # Entry point: collect → embed → query
├── youtube_transcript.ipynb        # Prototype notebook: fetch & inspect transcripts interactively
├── config/
│   └── config.py                   # Pydantic Settings (all config + .env overrides)
├── src/
│   ├── youtube_transcripts/
│   │   └── youtube_transcript.py   # YouTubeTranscriptCollector — fetch & retry
│   ├── database/
│   │   └── transcript_db.py        # TranscriptDatabase — persist & load raw transcripts (SQLite)
│   ├── embeddings/
│   │   ├── chunker.py              # chunk_text() — character-based overlap chunking
│   │   └── vector_store.py         # VectorStore — embed, upsert, query
│   └── utils/
│       └── logger.py               # Shared logger
├── data/                           # Persistent data files (gitignored)
│   ├── chroma_db/                  # ChromaDB vector store
│   └── transcripts.db              # SQLite transcript database
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
       ▼
VectorStore.add_from_dataframe()       — chunks, embeds, upserts into ChromaDB
       │
       ▼
ChromaDB (./data/chroma_db)
       │
       ▼
VectorStore.query(text)                — cosine similarity search → ranked results
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
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Overlapping characters between chunks |
| `VECTOR_DB_PATH` | `./data/chroma_db` | ChromaDB persistence directory |
| `COLLECTION_NAME` | `pokemon_tcg_transcripts` | ChromaDB collection name |
| `TRANSCRIPT_DB_PATH` | `./data/transcripts.db` | SQLite transcript database path |

## Features Completed

- [x] YouTube transcript collection with channel-based pagination
- [x] API rate limiting: configurable delay between transcript fetches
- [x] Retry logic: exponential backoff + jitter for transient HTTP/transcript errors
- [x] Character-based text chunking with configurable overlap
- [x] Local sentence-transformer embedding (no external API)
- [x] Persistent ChromaDB vector store with idempotent ingestion
- [x] Semantic query with optional metadata filtering
- [x] SQLite transcript database: raw transcript storage with idempotent inserts, independent of ChromaDB

## Documentation

Feature docs live in [`docs/`](docs/):

- [`youtube-transcript.md`](docs/youtube-transcript.md) — production module reference: `YouTubeTranscriptCollector` class, methods, output schema, retry helpers, proxy config
- [`api-rate-limiting.md`](docs/api-rate-limiting.md) — rate limiting, retry logic, error handling table
- [`embeddings-and-vector-store.md`](docs/embeddings-and-vector-store.md) — chunking, embedding model, ChromaDB schema, query format
- [`sqlite-transcript-database.md`](docs/sqlite-transcript-database.md) — `TranscriptDatabase` class, schema, idempotent save/load, design decisions
