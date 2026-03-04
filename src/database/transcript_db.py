"""SQLite persistence layer for YouTube transcript DataFrames."""

import sqlite3
from datetime import datetime, timezone
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

    _CREATE_SUMMARIES_TABLE = """
        CREATE TABLE IF NOT EXISTS summaries (
            video_id        TEXT PRIMARY KEY REFERENCES transcripts(video_id),
            summary         TEXT NOT NULL,
            model_used      TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            refined_summary TEXT,
            refined_at      TEXT
        )
    """

    _CREATE_VERIFICATIONS_TABLE = """
        CREATE TABLE IF NOT EXISTS verifications (
            video_id             TEXT PRIMARY KEY REFERENCES transcripts(video_id),
            verification_report  TEXT NOT NULL,
            sources              TEXT NOT NULL,
            price_data           TEXT NOT NULL,
            model_used           TEXT NOT NULL,
            verified_at          TEXT NOT NULL
        )
    """

    def __init__(self) -> None:
        self.db_path = Path(settings.transcript_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(self._CREATE_TABLE)
            conn.execute(self._CREATE_SUMMARIES_TABLE)
            conn.execute(self._CREATE_VERIFICATIONS_TABLE)
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

    def save_summary(self, video_id: str, summary: str, model_used: str) -> bool:
        """Persist a summary for a video. Skips silently if one already exists (INSERT OR IGNORE).

        Returns True if a new row was inserted, False if skipped.
        """
        created_at = datetime.now(timezone.utc).isoformat()
        sql = """
            INSERT OR IGNORE INTO summaries (video_id, summary, model_used, created_at)
            VALUES (?, ?, ?, ?)
        """
        with self._connect() as conn:
            cursor = conn.execute(sql, (video_id, summary, model_used, created_at))
            inserted = cursor.rowcount == 1
        if inserted:
            logger.info(
                f"save_summary() — saved summary for {video_id} via {model_used}."
            )
        else:
            logger.debug(
                f"save_summary() — summary for {video_id} already exists, skipped."
            )
        return inserted

    def load_summaries(self) -> pd.DataFrame:
        """Return the full summaries table as a DataFrame."""
        with self._connect() as conn:
            df = pd.read_sql_query("SELECT * FROM summaries", conn)
        logger.info(f"load_summaries() — returned {len(df)} row(s).")
        return df

    def get_unsummarized_transcripts(self) -> pd.DataFrame:
        """Return transcripts with no summary row and transcript_available = 1."""
        sql = """
            SELECT t.*
            FROM transcripts t
            LEFT JOIN summaries s ON t.video_id = s.video_id
            WHERE s.video_id IS NULL
              AND t.transcript_available = 1
        """
        with self._connect() as conn:
            df = pd.read_sql_query(sql, conn)
        if not df.empty:
            df["transcript_available"] = df["transcript_available"].astype(bool)
        logger.info(
            f"get_unsummarized_transcripts() — {len(df)} transcript(s) pending summarization."
        )
        return df

    def get_unverified_summaries(self) -> pd.DataFrame:
        """Return summaries with no verification row, joined with their transcript."""
        sql = """
            SELECT s.video_id, s.summary, t.transcript, t.title, t.channel
            FROM summaries s
            JOIN transcripts t ON s.video_id = t.video_id
            LEFT JOIN verifications v ON s.video_id = v.video_id
            WHERE v.video_id IS NULL
        """
        with self._connect() as conn:
            df = pd.read_sql_query(sql, conn)
        logger.info(
            f"get_unverified_summaries() — {len(df)} summary/summaries pending verification."
        )
        return df

    def save_verification(
        self,
        video_id: str,
        verification_report: str,
        sources: str,
        price_data: str,
        model_used: str,
    ) -> bool:
        """Persist a verification result. Skips silently if one already exists.

        Returns True if a new row was inserted, False if skipped.
        """
        verified_at = datetime.now(timezone.utc).isoformat()
        sql = """
            INSERT OR IGNORE INTO verifications
                (video_id, verification_report, sources, price_data, model_used, verified_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            cursor = conn.execute(
                sql,
                (
                    video_id,
                    verification_report,
                    sources,
                    price_data,
                    model_used,
                    verified_at,
                ),
            )
            inserted = cursor.rowcount == 1
        if inserted:
            logger.info(f"save_verification() — saved verification for {video_id}.")
        else:
            logger.debug(
                f"save_verification() — verification for {video_id} already exists, skipped."
            )
        return inserted

    def save_refined_summary(self, video_id: str, refined_summary: str) -> None:
        """Update the summaries row with a refined summary from the feedback loop."""
        refined_at = datetime.now(timezone.utc).isoformat()
        sql = """
            UPDATE summaries
            SET refined_summary = ?, refined_at = ?
            WHERE video_id = ?
        """
        with self._connect() as conn:
            conn.execute(sql, (refined_summary, refined_at, video_id))
        logger.info(f"save_refined_summary() — updated refined summary for {video_id}.")
