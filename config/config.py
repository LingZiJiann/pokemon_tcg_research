from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env"
    )

    web_share_username: str
    web_share_pw: str
    youtube_api_key: str
    channels: list[str] = [
        "@TwicebakedJake",
        "@okJLUV",
    ]
    max_videos_per_channel: int = 1
    language: str = "en"


settings = Settings()
