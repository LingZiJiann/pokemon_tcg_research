# Coding Conventions

**Analysis Date:** 2026-02-27

## Naming Patterns

**Files:**
- Module files: `snake_case` (e.g., `logger.py`, `youtube_transcript.py`)
- Config files: `snake_case` (e.g., `config.py`)
- Main entry point: `main.py`

**Functions:**
- Private methods: `_snake_case()` prefix (e.g., `_resolve_channel_id()`, `_get_transcript()`)
- Public methods: `snake_case()` (e.g., `collect()`, `setup_logger()`)
- Function names are descriptive and action-oriented (verb-first pattern)

**Variables:**
- Local variables: `snake_case` (e.g., `channel_id`, `transcript`, `all_records`)
- Constants: `SCREAMING_SNAKE_CASE` (not heavily used in current codebase)
- Dictionary keys: `snake_case` (e.g., `"channel_id"`, `"published_at"`, `"transcript_available"`)
- Loop variables use descriptive names (e.g., `for channel_input in self.channels`, `for video in tqdm(videos)`)

**Classes:**
- Class names: `PascalCase` (e.g., `YouTubeTranscriptCollector`, `Settings`)

**Types:**
- Type hints are used extensively with Python 3.10+ union syntax
- Example: `str | None`, `list[str]`, `list[dict]`
- Return types are explicitly declared (e.g., `-> pd.DataFrame`, `-> str | None`)

## Code Style

**Formatting:**
- Python version: 3.10+ required (`requires-python = ">=3.10"`)
- Line length: Not explicitly configured but code follows reasonable limits
- Black is included in dev dependencies for code formatting
- Ruff is included in dev dependencies for linting

**Linting:**
- Ruff is the linter (defined in `pyproject.toml` dev dependencies)
- Black is the code formatter
- Configuration: Not explicitly configured in `pyproject.toml` (uses defaults)

## Import Organization

**Order:**
1. Standard library imports (e.g., `import logging`, `import time`, `from datetime import datetime`, `from pathlib import Path`)
2. Third-party imports (e.g., `import pandas as pd`, `from googleapiclient.discovery import build`, `from tqdm.auto import tqdm`)
3. Local application imports (e.g., `from config.config import settings`, `from src.utils.logger import get_logger`)

**Path Aliases:**
- Uses absolute imports from project root (e.g., `from config.config import settings`, `from src.utils.logger import get_logger`)
- No aliases or `sys.path` manipulation detected

**Spacing:**
- Imports separated by blank line between groups
- Example from `youtube_transcript.py`:
  - Standard library imports
  - (blank line)
  - Third-party imports
  - (blank line)
  - Local imports

## Error Handling

**Patterns:**
- Specific exception catching: `except (NoTranscriptFound, TranscriptsDisabled)` in `_get_transcript()`
- Generic exception catching with logging: `except Exception as e: logger.warning(...)`
- Exception messages include context: `logger.error("Could not fetch channel %s: %s", channel_input, e)`
- Graceful degradation: Returns `None` when transcript unavailable rather than raising
- Exception handling with continue: `except Exception as e: ... continue` in loop contexts (`collect()` method)
- No raise statements with custom exceptions detected

## Logging

**Framework:** Standard library `logging` module

**Patterns:**
- Logger created per module using `get_logger(__name__)`
- Example: `logger = get_logger("youtube_transcript")` at module level
- Log levels used: `INFO` (default), `WARNING`, `ERROR`
- String formatting: Uses `%` style (e.g., `logger.info("Processing channel: %s", channel_input)`)
- Contextual logging: Includes relevant variables in log messages
- Logger initialization: Custom `setup_logger()` function in `src/utils/logger.py` with file and console handlers

**Log format:**
- File logs (detailed): `%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s`
- Console logs (simple): `%(asctime)s - %(levelname)s - %(message)s`

## Comments

**When to Comment:**
- Detailed docstrings for all public methods and functions
- No inline comments in current code (logic is clear from names)
- Commented-out code present: `# from youtube_transcript_api.proxies import WebshareProxyConfig` (indicates future feature)

**JSDoc/TSDoc:**
- Python docstrings using Google-style format for all public methods
- Example from `_resolve_channel_id()`:
  ```python
  """
  Resolve a YouTube channel handle or ID to its channel ID and title.

  This function takes either a full channel ID (starting with 'UC') or a
  channel handle (starting with '@') and returns a dictionary containing
  the channel ID and the channel's title.

  Args:
      channel_input (str): The YouTube channel identifier...

  Returns:
      dict: A dictionary with keys:
          - 'channel_id' (str): The YouTube channel's unique ID.
          - 'channel_title' (str): The title of the channel.
  """
  ```
- Docstrings include Args, Returns, and description sections

## Function Design

**Size:** Methods are moderate in length (15-60 lines) with clear single responsibilities

**Parameters:**
- Type hints for all parameters (e.g., `name: str`, `log_level: int = logging.INFO`)
- Default values provided where sensible (e.g., `log_dir: str = "logs"`, `console_output: bool = True`)
- Dictionary unpacking used when extracting multiple fields (e.g., `channel_id = channel_info["channel_id"]`)

**Return Values:**
- Explicit return type hints on all functions
- Meaningful return values (DataFrames, dicts, strings, None)
- Union types used for optional returns (e.g., `-> str | None`)

## Module Design

**Exports:**
- Functional modules export specific functions (e.g., `setup_logger()`, `get_logger()`)
- Class-based modules export the main class (e.g., `YouTubeTranscriptCollector`)
- Configuration exposed as singleton instance: `settings = Settings()`

**Barrel Files:**
- No `__init__.py` files found in directories
- Direct imports from module files required (e.g., `from src.utils.logger import get_logger`)

---

*Convention analysis: 2026-02-27*
