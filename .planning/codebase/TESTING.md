# Testing Patterns

**Analysis Date:** 2026-02-27

## Test Framework

**Runner:**
- pytest >= 7.0 (defined in `pyproject.toml` dev dependencies)
- Config: Not detected (uses pytest defaults)

**Assertion Library:**
- pytest built-in assertions (no additional assertion library configured)

**Run Commands:**
```bash
pytest                          # Run all tests (when test files exist)
pytest -v                       # Verbose output
pytest --cov                    # Coverage (if pytest-cov installed)
```

**Note:** No test configuration file (`pytest.ini`, `setup.cfg`, or `[tool.pytest.ini_options]` in `pyproject.toml`) found.

## Test File Organization

**Location:**
- **Currently:** No test files detected in codebase
- **Expected pattern:** Co-located with source code or in separate `tests/` directory

**Naming:**
- Convention defined in dependencies: Tests should follow `test_*.py` or `*_test.py` pattern

**Status:**
- Testing infrastructure configured in `pyproject.toml` but no test files implemented
- This is a testing gap that should be addressed

## Test Structure

**Expected Pattern (based on project setup):**
```python
def test_function_name():
    # Arrange
    # Act
    # Assert
    pass
```

**Current State:**
No test files exist to demonstrate actual patterns. The following patterns should be implemented:

## Mocking

**Framework:** Not configured
- `unittest.mock` (standard library) would be available if tests were written
- No mocking library (pytest-mock, etc.) in dev dependencies

**Recommended approach for YouTube API testing:**
```python
from unittest.mock import Mock, patch

def test_resolve_channel_id():
    with patch('src.youtube_transcripts.youtube_transcript.build') as mock_build:
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        # Test implementation
```

**What to Mock:**
- External API calls (YouTube API via `googleapiclient`)
- Network requests (transcript API calls)
- File I/O (logger file operations)
- Configuration loading

**What NOT to Mock:**
- Internal method calls between project modules
- Pydantic Settings validation
- Logger setup (can use caplog fixture)

## Fixtures and Factories

**Test Data:**
- Not implemented
- Recommended pattern for YouTube transcripts:
```python
@pytest.fixture
def sample_video():
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Test Video",
        "published_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_transcript():
    return "This is a sample transcript text."
```

**Location:**
- Would typically be in `tests/conftest.py` for shared fixtures
- Test-specific factories in individual test modules

## Coverage

**Requirements:** Not enforced
- No coverage thresholds defined in `pyproject.toml`
- Coverage tools not installed (would need `pytest-cov`)

**View Coverage:**
```bash
# Install coverage first
pip install pytest-cov

# Run with coverage
pytest --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and methods (e.g., `_resolve_channel_id()`, `setup_logger()`)
- Approach: Test with mocked dependencies, focus on logic and error handling
- Example targets:
  - `YouTubeTranscriptCollector._resolve_channel_id()` - test channel ID validation
  - `YouTubeTranscriptCollector._get_transcript()` - test transcript fetching and fallback logic
  - `setup_logger()` - test logger configuration

**Integration Tests:**
- Scope: Multiple components working together (e.g., logger setup + usage)
- Approach: Use real file I/O for logger, mock YouTube API
- Example targets:
  - Logger initialization with file creation
  - Configuration loading with environment variables
  - YouTubeTranscriptCollector initialization with settings

**E2E Tests:**
- Framework: Not configured
- Status: Would require live YouTube API or comprehensive mocking
- Recommendation: Not practical without separating API concerns

## Common Patterns

**Async Testing:**
- Not applicable - no async code in current codebase
- All API calls use synchronous `googleapiclient` library

**Error Testing:**
```python
# Recommended pattern for exception testing
import pytest

def test_transcript_not_found():
    with pytest.raises(NoTranscriptFound):
        # Test code that should raise

def test_channel_resolution_with_invalid_id():
    with pytest.raises(ValueError, match="Channel not found"):
        # Test invalid channel input
```

**Mocking External Services:**
```python
@patch('src.youtube_transcripts.youtube_transcript.YouTubeTranscriptApi')
def test_get_transcript_with_fallback(mock_api_class):
    mock_api = Mock()
    mock_api_class.return_value = mock_api

    # Setup transcript list mock
    mock_transcript_list = Mock()
    mock_api.list.return_value = mock_transcript_list

    # Test the fallback from manual to generated transcript
```

**Testing with Settings:**
```python
@pytest.fixture
def mock_settings():
    with patch('config.config.settings') as mock:
        mock.youtube_api_key = "test_key"
        mock.channels = ["@testchannel"]
        mock.max_videos_per_channel = 1
        yield mock

def test_collector_initialization(mock_settings):
    collector = YouTubeTranscriptCollector()
    assert collector.channels == ["@testchannel"]
```

## Current Testing Gap

**Critical issues:**
1. No test files exist despite pytest being configured
2. External API integration (`YouTubeTranscriptCollector`) is untested
3. Error handling paths not validated
4. Logger functionality not validated
5. Configuration loading not tested

**Priority fixes:**
1. Create `tests/` directory structure
2. Add unit tests for `YouTubeTranscriptCollector` methods with mocked API
3. Add tests for error handling (missing transcripts, invalid channels)
4. Add configuration validation tests
5. Configure coverage tracking in `pyproject.toml`

---

*Testing analysis: 2026-02-27*
