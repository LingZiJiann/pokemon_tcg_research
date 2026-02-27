# Embeddings & Vector Store

## Overview

Transcript text is embedded using a local sentence-transformer model and stored in a persistent ChromaDB vector database. This enables semantic search over collected Pokemon TCG YouTube transcripts.

## Architecture

```
DataFrame (transcripts)
        │
        ▼
   chunker.py          — split transcript text into overlapping character chunks
        │
        ▼
SentenceTransformer    — encode chunks into dense float vectors
        │
        ▼
  ChromaDB collection  — persist vectors + metadata to disk
        │
        ▼
  VectorStore.query()  — cosine similarity search at query time
```

## Components

### `src/embeddings/chunker.py`

Single function: `chunk_text(text, chunk_size, chunk_overlap) -> list[str]`

Splits raw transcript text into overlapping character-based chunks. Character-based splitting (rather than sentence or word splitting) is intentional — YouTube transcripts often lack punctuation, so fixed-size character windows with overlap prevent cutting mid-thought.

| Parameter | Config key | Default | Description |
|---|---|---|---|
| `chunk_size` | `chunk_size` | `500` | Characters per chunk |
| `chunk_overlap` | `chunk_overlap` | `100` | Characters of overlap between adjacent chunks |

### `src/embeddings/vector_store.py`

`VectorStore` class — wraps ChromaDB and the embedding model.

**Initialization:**

```python
store = VectorStore()
```

Creates (or opens) a persistent ChromaDB client at `settings.vector_db_path` and loads the sentence-transformer model specified by `settings.embedding_model`.

**Methods:**

| Method | Description |
|---|---|
| `add_from_dataframe(df)` | Chunk, embed, and upsert all rows with `transcript_available == True`. Skips videos already in the collection (idempotent). |
| `query(text, n_results, where)` | Embed `text` and return the top-n most similar chunks. Optional `where` dict filters by metadata (e.g. `{"channel": "TwicebakedJake"}`). |
| `_already_stored(video_id)` | Internal check — returns `True` if any chunk for a `video_id` exists in the collection. |

**`add_from_dataframe` expected DataFrame columns:**

`video_id`, `title`, `transcript`, `transcript_available`, `channel`, `channel_id`, `published_at`, `url`

**`query` return format:**

```python
[
    {
        "text": "<chunk text>",
        "metadata": {
            "channel": "...",
            "channel_id": "...",
            "video_id": "...",
            "title": "...",
            "published_at": "...",
            "url": "...",
            "chunk_index": 0,
            "total_chunks": 12,
        },
        "distance": 0.12,   # cosine distance — lower is more similar
    },
    ...
]
```

## Configuration

All settings live in `config/config.py` and can be overridden via `.env`:

| Setting | Default | Description |
|---|---|---|
| `embedding_model` | `all-MiniLM-L6-v2` | Sentence-transformers model name |
| `chunk_size` | `500` | Characters per chunk |
| `chunk_overlap` | `100` | Overlapping characters between chunks |
| `vector_db_path` | `./chroma_db` | Directory where ChromaDB persists data |
| `collection_name` | `pokemon_tcg_transcripts` | ChromaDB collection name |

`.env` example:

```
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=100
VECTOR_DB_PATH=./chroma_db
COLLECTION_NAME=pokemon_tcg_transcripts
```

## Embedding Model

Model: [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

- 384-dimensional dense vectors
- Runs fully locally via `sentence-transformers`
- No API key or network access required after initial download

## Vector Database

Database: [ChromaDB](https://www.trychroma.com/) (persistent mode)

- Stored on disk at `vector_db_path` — survives process restarts
- Similarity metric: **cosine distance** (`hnsw:space: cosine`)
- Each chunk is stored with its full metadata for attribution

## Design Decisions

- **Idempotent ingestion** — `_already_stored` checks by `video_id` before embedding, so re-running the pipeline never duplicates data.
- **Character-based chunking** — transcript text lacks punctuation, making sentence/word splitting unreliable. Fixed-size windows with overlap are more predictable.
- **Local embedding model** — avoids external API calls and per-token costs. `all-MiniLM-L6-v2` is small (22M params) and fast enough for offline batch ingestion.
- **Metadata stored per chunk** — every chunk carries `channel`, `video_id`, `title`, `url`, etc. so query results are immediately attributable without a secondary lookup.
