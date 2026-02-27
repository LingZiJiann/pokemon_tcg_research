# Codebase Structure

**Analysis Date:** 2026-02-27

## Directory Layout

```
pokemon_tcg_research/
├── main.py                          # Entry point - runs transcript collection
├── pyproject.toml                   # Project metadata and dependencies
├── .gitignore                       # Git ignore rules
├── .env                             # Environment variables (not committed)
├── config/
│   └── config.py                    # Pydantic Settings configuration model
├── src/
│   ├── youtube_transcripts/
│   │   └── youtube_transcript.py    # YouTubeTranscriptCollector class
│   └── utils/
│       └── logger.py                # Logging setup and factory functions
├── logs/                            # Generated log files (not committed)
├── .vscode/                         # VS Code settings (not committed)
└── .planning/
    └── codebase/                    # Planning documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
```

## Directory Purposes

**config:**
- Purpose: Store application configuration and settings
- Contains: Configuration models using Pydantic
- Key files: `config.py` - Pydantic Settings model that loads YouTube API key and collection parameters from environment

**src:**
- Purpose: Core application source code organized by feature/domain
- Contains: Feature modules and shared utilities
- Key files: None at root level (feature-specific code in subdirectories)

**src/youtube_transcripts:**
- Purpose: YouTube data collection functionality
- Contains: Classes and methods for collecting transcripts from YouTube channels
- Key files: `youtube_transcript.py` - Defines YouTubeTranscriptCollector class

**src/utils:**
- Purpose: Shared utilities and cross-cutting concerns
- Contains: Helper functions and utility classes used across the application
- Key files: `logger.py` - Logging setup and configuration

**logs:**
- Purpose: Store generated application logs
- Generated: Yes - created at runtime by logger
- Committed: No - entries in .gitignore

## Key File Locations

**Entry Points:**
- `main.py`: Primary script entry point. Instantiates YouTubeTranscriptCollector and calls collect() method

**Configuration:**
- `config/config.py`: Pydantic Settings model defining all configuration parameters
- `.env`: Environment variable file (not committed) containing secrets and API keys

**Core Logic:**
- `src/youtube_transcripts/youtube_transcript.py`: YouTubeTranscriptCollector class containing all YouTube API interaction logic

**Utilities:**
- `src/utils/logger.py`: Logging infrastructure with setup_logger() and get_logger() functions

## Naming Conventions

**Files:**
- `snake_case.py` - Python modules (e.g., `youtube_transcript.py`, `logger.py`)
- `UPPERCASE.md` - Documentation files (e.g., `ARCHITECTURE.md`, `STRUCTURE.md`)

**Directories:**
- `snake_case/` - Module directories (e.g., `youtube_transcripts`, `utils`)
- `lowercase/` - Configuration and special directories (e.g., `config`, `logs`)
- `.hidden/` - Hidden directories prefixed with dot (e.g., `.planning`, `.vscode`)

**Classes:**
- `PascalCase` - Class names (e.g., `YouTubeTranscriptCollector`, `Settings`)

**Functions:**
- `snake_case()` - Function names (e.g., `setup_logger()`, `get_logger()`, `collect()`)

**Methods:**
- `snake_case()` - Public methods (e.g., `collect()`, `_resolve_channel_id()`)
- `_snake_case()` - Private methods with leading underscore (e.g., `_get_transcript()`, `_get_videos_from_playlist()`)

**Variables/Constants:**
- `snake_case` - Variable names (e.g., `channel_id`, `transcript_list`)
- `UPPER_CASE` - Configuration constants (e.g., log levels in logger.py)

## Where to Add New Code

**New YouTube Collection Feature:**
- Primary code: `src/youtube_transcripts/youtube_transcript.py` - Add new methods to YouTubeTranscriptCollector class
- Alternative: If feature is unrelated to YouTube API, create new module in `src/` (e.g., `src/sentiment_analysis/` for sentiment analysis)

**New Utility/Helper Function:**
- Shared helpers: `src/utils/` - Create or add to appropriate module
- Example: If adding database utility, create `src/utils/database.py`

**New Configuration Parameter:**
- Add to: `config/config.py` - Add field to Settings class with appropriate type and default value
- Example: `sentiment_model_path: str = "models/sentiment.pkl"`

**New Module/Package:**
- Location: `src/[module_name]/` - Create directory under src with appropriate name
- Implementation: Create `[module].py` file inside the directory
- Initialization: No `__init__.py` files currently used (namespace packages assumed in Python 3.3+)

## Special Directories

**logs:**
- Purpose: Store application log files generated at runtime
- Generated: Yes - created by logger setup function if not present
- Committed: No - all files ignored via .gitignore

**.planning:**
- Purpose: Store planning and codebase analysis documents
- Generated: Yes - created by GSD mapping and planning tools
- Committed: Yes - documents are tracked for collaborative reference
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, STACK.md, INTEGRATIONS.md, CONCERNS.md

**.vscode:**
- Purpose: Store VS Code editor configuration and settings
- Generated: No - created manually by user
- Committed: No - ignored via .gitignore

**__pycache__:**
- Purpose: Store compiled Python bytecode for faster imports
- Generated: Yes - created automatically by Python at runtime
- Committed: No - ignored via .gitignore (entries: `__pycache__/`, `**/__pycache__/`)

## Module Organization

**No __init__.py files:**
The codebase does not use `__init__.py` files, relying on namespace packages (Python 3.3+ default behavior). This means:
- Modules can be imported as `from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector`
- No package initialization code is required
- Scripts should be run with working directory at project root

**Import Style:**
- Absolute imports from project root (e.g., `from config.config import settings`, `from src.utils.logger import get_logger`)
- No relative imports currently used
- External dependencies: standard library, pandas, Google API client, youtube-transcript-api, pydantic, tqdm

---

*Structure analysis: 2026-02-27*
