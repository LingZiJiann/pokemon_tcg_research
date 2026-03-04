from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env")

    # Credentials for web share access
    web_share_username: str
    web_share_pw: str

    # YouTube Data API v3 key for fetching channel/video metadata
    youtube_api_key: str

    # List of YouTube channel handles to scrape transcripts from
    channels: list[str] = [
        "@TwicebakedJake",
        "@@DannyPhantump",
    ]

    # Maximum number of recent videos to process per channel
    max_videos_per_channel: int = 1

    # Preferred transcript language (ISO 639-1 code)
    language: str = "en"

    # Rate limiting & retry settings
    transcript_delay: float = 2
    api_max_retries: int = 3
    api_retry_base_delay: float = 2.0
    api_retry_max_delay: float = 60.0

    # SQLite transcript store
    transcript_db_path: str = "./data/transcripts.db"

    # AI Summarization
    anthropic_api_key: str | None = None
    claude_model: str = "claude-haiku-4-5-20251001"
    ollama_model: str = "gpt-oss:20b"
    ollama_base_url: str = "http://localhost:11434"
    summary_max_tokens: int = 1024

    # Verification agent (Tavily)
    tavily_api_key: str
    max_cards_per_verification: int = 5
    verification_search_depth: str = "basic"


settings = Settings()
