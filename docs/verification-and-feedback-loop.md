# Verification Agent & Feedback Loop

## Overview

After each summarization run, a verification agent cross-checks the AI-generated summary against real-world market data. It searches Tavily (general market) and eBay last-sold listings (via Tavily) for every card mentioned in the summary, then feeds the findings back to Claude to produce a **refined summary** — the feedback loop.

Results are persisted to two new structures in `data/transcripts.db`:
- A `verifications` table storing the price report, sources, and raw price data per video.
- Two new columns on the existing `summaries` table: `refined_summary` and `refined_at`.

## Architecture

```
TranscriptDatabase.get_unverified_summaries()
        │
        ▼
  pandas DataFrame  (summaries with no row in verifications)
        │
        ▼
TranscriptVerifier._extract_cards(summary)
        │  Claude Haiku extracts [{card_name, claimed_price}, ...]
        ▼
For each card (up to max_cards_per_verification):
        │
        ├──► Tavily search: "{card} pokemon tcg card price"
        └──► Tavily search: "{card} pokemon card sold completed site:ebay.com"
        │
        ▼
TranscriptDatabase.save_verification()   — INSERT OR IGNORE into verifications
        │
        ▼
TranscriptVerifier._refine_summary()     — Claude re-prompted with initial summary + verification report
        │
        ▼
TranscriptDatabase.save_refined_summary()  — UPDATE summaries SET refined_summary, refined_at
```

## Components

### `src/verifier/verifier.py`

`TranscriptVerifier` class — orchestrates verification and the feedback loop.

**Initialization:**

```python
verifier = TranscriptVerifier(db=db)   # pass existing TranscriptDatabase instance
# or
verifier = TranscriptVerifier()         # creates its own TranscriptDatabase
```

**Methods:**

| Method | Description |
|---|---|
| `run()` | Verify all unverified summaries. Returns count processed. Idempotent. Skips silently if `TAVILY_API_KEY` is not set. |
| `_verify_summary(summary)` | Extracts cards, runs Tavily searches, returns `{price_data, sources, report}`. |
| `_extract_cards(summary)` | Asks Claude Haiku to extract a JSON list of `{card_name, claimed_price}` from the summary text. |
| `_search_card_prices(card_name)` | Runs two Tavily searches (general market + eBay sold) for one card. Returns `(snippets, sources)`. |
| `_refine_summary(initial_summary, verification)` | Re-prompts Claude with the initial summary and verification report to produce a grounded refined summary. Falls back to the initial summary if Claude fails. |

## Database Schema

### New table: `verifications`

| Column | SQLite Type | Description |
|---|---|---|
| `video_id` | `TEXT PRIMARY KEY` | FK to `transcripts.video_id` |
| `verification_report` | `TEXT NOT NULL` | Markdown report of findings per card |
| `sources` | `TEXT NOT NULL` | JSON array of source URLs from Tavily |
| `price_data` | `TEXT NOT NULL` | JSON object: `{"Card Name": "price snippet"}` |
| `model_used` | `TEXT NOT NULL` | Claude model used for card extraction |
| `verified_at` | `TEXT NOT NULL` | UTC ISO 8601 timestamp |

### Updated table: `summaries`

Two new nullable columns added via idempotent `ALTER TABLE` migration on startup:

| Column | SQLite Type | Description |
|---|---|---|
| `refined_summary` | `TEXT` | Claude-refined summary incorporating verified price data |
| `refined_at` | `TEXT` | UTC ISO 8601 timestamp of the refinement |

### New `TranscriptDatabase` methods

| Method | Description |
|---|---|
| `get_unverified_summaries()` | LEFT JOIN summaries → verifications. Returns rows with no verification, joined to the original transcript. |
| `save_verification(video_id, report, sources, price_data, model_used)` | `INSERT OR IGNORE` into `verifications`. Returns `True` if inserted. |
| `save_refined_summary(video_id, refined_summary)` | `UPDATE summaries` to set `refined_summary` and `refined_at`. |

## Prompt Templates

### Card extraction prompt

Instructs Claude to return a JSON array of `{card_name, claimed_price}` objects from the summary text. Response is parsed with `json.loads()`. Markdown code fences are stripped if present.

### Refinement prompt (feedback loop)

Instructs Claude to refine the initial summary by:
- Incorporating verified prices where the Tavily data confirms or updates the claim
- Correcting discrepancies found by the verification
- Noting cards whose prices could not be verified
- Keeping the same structured format as the initial summary

## Tavily Searches

Two searches are run per card:

| Query | Purpose |
|---|---|
| `{card} pokemon tcg card price` | General market — finds price guides, recent sales, community pricing |
| `{card} pokemon card sold completed site:ebay.com` | eBay last-sold — surfaces recently completed auction and buy-it-now prices |

`max_results=3` per search. Up to `max_cards_per_verification` cards are searched per video (default 5), capping total Tavily API calls at `2 × 5 = 10` per video.

## Idempotency

- `get_unverified_summaries()` gates entry via a `LEFT JOIN`: only summaries with no row in `verifications` are returned.
- `save_verification()` uses `INSERT OR IGNORE`: re-running never creates duplicate verification rows.
- `save_refined_summary()` uses `UPDATE`, so it overwrites if re-run (only reachable after a fresh verification insert anyway).
- A video that fails verification is not inserted into `verifications`, so it will be retried on the next run.

## Graceful Degradation

- If `TAVILY_API_KEY` is not set, `run()` logs a warning and returns `0` — the rest of the pipeline is unaffected.
- If card extraction fails (Claude error, JSON parse error), verification proceeds with an empty card list and a `"No cards identified"` report.
- If a Tavily search fails for an individual card, it is skipped and the other cards are still processed.
- If the refinement Claude call fails, `_refine_summary()` returns the original initial summary unchanged.

## Usage

```python
from src.database.transcript_db import TranscriptDatabase
from src.verifier.verifier import TranscriptVerifier

db = TranscriptDatabase()
verifier = TranscriptVerifier(db=db)
n = verifier.run()
print(f"{n} summary/summaries verified and refined.")

# Inspect results
summaries = db.load_summaries()
print(summaries[['video_id', 'summary', 'refined_summary', 'refined_at']])
```

To inspect verifications directly, query the `verifications` table via SQLite:

```python
import sqlite3, json
conn = sqlite3.connect("data/transcripts.db")
for row in conn.execute("SELECT video_id, price_data, verified_at FROM verifications"):
    print(row[0], json.loads(row[1]))
```

## Configuration

| Setting | `.env` key | Default | Description |
|---|---|---|---|
| `tavily_api_key` | `TAVILY_API_KEY` | `""` | Tavily API key. If empty, the verification stage is skipped. |
| `max_cards_per_verification` | `MAX_CARDS_PER_VERIFICATION` | `5` | Max number of cards to search per video. Caps Tavily API usage. |
| `verification_search_depth` | `VERIFICATION_SEARCH_DEPTH` | `"basic"` | Tavily search depth: `"basic"` or `"advanced"`. Advanced returns richer snippets at higher cost. |

Add to `.env`:

```
TAVILY_API_KEY=tvly-...
```

## Installation

```bash
uv sync
# or
pip install tavily-python
```

## Design Decisions

- **Tavily for eBay** — eBay's public Finding API for completed listings was deprecated. Using Tavily to search `site:ebay.com` sold listings is simpler (no extra credentials) and produces usable price snippets for the refinement prompt.
- **Separate `verifications` table** — Keeps verification data independent of the summary. Verification can be re-run as prices change without touching the original summary.
- **`refined_summary` as a column, not a separate table** — Refined summaries are a 1:1 update to the existing summary row. A separate table would add a join with no benefit.
- **Idempotent migration** — On startup, `TranscriptDatabase` checks `PRAGMA table_info(summaries)` before issuing `ALTER TABLE`, so existing databases with the old schema are upgraded safely on first run.
- **Lazy client construction** — Both `anthropic.Anthropic()` and `TavilyClient()` are constructed only on first use, keeping startup cost low and making API key errors visible at the point of use.
- **Card count cap** — `max_cards_per_verification` (default 5) prevents runaway API usage on transcripts that mention dozens of cards.
