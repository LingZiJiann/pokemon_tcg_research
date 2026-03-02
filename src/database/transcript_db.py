"""SQLite persistence layer for YouTube transcript DataFrames."""

import sqlite3
from pathlib import Path

import pandas as pd

from config.config import settings
from src.utils.logger import get_logger

logger = get_logger("transcript_db")


class TranscriptDatabase:
    """Persist and reload the raw transcript DataFrame using SQLite."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS transcripts (
            video_id              TEXT PRIMARY KEY,
            channel               TEXT,
            channel_id            TEXT,
            title                 TEXT,
            published_at          TEXT,
            url                   TEXT,
            transcript            TEXT,
            transcript_available  INTEGER
        )
    """

    def __init__(self) -> None:
        self.db_path = Path(settings.transcript_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(self._CREATE_TABLE)
        logger.info(f"TranscriptDatabase ready — {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, df: pd.DataFrame) -> int:
        """Insert new rows, skipping any video_id already stored. Returns new row count."""
        if df.empty:
            return 0
        records = [
            (
                row["video_id"],
                row["channel"],
                row["channel_id"],
                row["title"],
                row["published_at"],
                row["url"],
                row["transcript"],
                int(row["transcript_available"]),
            )
            for _, row in df.iterrows()
        ]
        sql = """
            INSERT OR IGNORE INTO transcripts
                (video_id, channel, channel_id, title,
                 published_at, url, transcript, transcript_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            cursor = conn.executemany(sql, records)
            new_rows = cursor.rowcount
        logger.info(
            f"save() — {new_rows} new row(s) inserted, {len(records) - new_rows} skipped."
        )
        return new_rows

    def load(self) -> pd.DataFrame:
        """Return full transcripts table as a DataFrame."""
        with self._connect() as conn:
            df = pd.read_sql_query("SELECT * FROM transcripts", conn)
        if not df.empty:
            df["transcript_available"] = df["transcript_available"].astype(bool)
        logger.info(f"load() — returned {len(df)} row(s).")
        return df
