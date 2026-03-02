"""AI summarization agent for Pokemon TCG YouTube transcripts.

Tries Claude (Anthropic) first; falls back to Ollama on any exception.
Persists results to the summaries table via TranscriptDatabase.
"""

import anthropic
import ollama

from config.config import settings
from src.database.transcript_db import TranscriptDatabase
from src.utils.logger import get_logger

logger = get_logger("summarizer")

_PROMPT_TEMPLATE = """\
You are an expert Pokemon Trading Card Game (TCG) analyst. \
Below is a transcript from a YouTube video by a Pokemon TCG content creator.

Your task is to write a concise, structured summary of the video. \
Focus specifically on:
- Cards or sets discussed (names, set symbols, rarity)
- Market price movements or valuations mentioned
- Investment advice or speculation (buy/hold/sell signals)
- Pack opening results and notable pulls
- Grading or PSA-related commentary
- Meta shifts or competitive deck recommendations
- Any specific price predictions or market sentiment expressed

Avoid generic filler. Be specific: name the cards, the prices, the sets.

VIDEO TITLE: {title}
CHANNEL: {channel}

TRANSCRIPT:
{transcript}

SUMMARY:"""


class TranscriptSummarizer:
    """Summarize raw transcripts using Claude with Ollama fallback.

    Usage:
        summarizer = TranscriptSummarizer()
        n = summarizer.run()
        print(f"Summarized {n} transcript(s).")
    """

    def __init__(self, db: TranscriptDatabase | None = None) -> None:
        self.db = db if db is not None else TranscriptDatabase()
        self._claude_client: anthropic.Anthropic | None = None

    def _build_prompt(self, title: str, channel: str, transcript: str) -> str:
        return _PROMPT_TEMPLATE.format(
            title=title, channel=channel, transcript=transcript
        )

    def _summarize_with_claude(self, prompt: str) -> str:
        if self._claude_client is None:
            self._claude_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )
        message = self._claude_client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.summary_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _summarize_with_ollama(self, prompt: str) -> str:
        response = ollama.chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": settings.summary_max_tokens},
        )
        return response["message"]["content"]

    def _summarize_one(
        self, video_id: str, title: str, channel: str, transcript: str
    ) -> tuple[str, str] | None:
        prompt = self._build_prompt(title=title, channel=channel, transcript=transcript)

        try:
            summary = self._summarize_with_claude(prompt)
            logger.info(
                f"_summarize_one() — Claude succeeded for '{title}' ({video_id})."
            )
            return summary, settings.claude_model
        except Exception as claude_err:
            logger.warning(
                f"_summarize_one() — Claude failed for '{title}' ({video_id}): "
                f"{type(claude_err).__name__}: {claude_err}. Falling back to Ollama."
            )

        try:
            summary = self._summarize_with_ollama(prompt)
            logger.info(
                f"_summarize_one() — Ollama succeeded for '{title}' ({video_id})."
            )
            return summary, settings.ollama_model
        except Exception as ollama_err:
            logger.error(
                f"_summarize_one() — Ollama also failed for '{title}' ({video_id}): "
                f"{type(ollama_err).__name__}: {ollama_err}. Skipping."
            )
            return None

    def run(self) -> int:
        """Summarize all transcripts not yet in the summaries table.

        Idempotent: uses get_unsummarized_transcripts() to skip already-summarized videos.
        Returns the number of summaries successfully saved in this run.
        """
        pending = self.db.get_unsummarized_transcripts()

        if pending.empty:
            logger.info("run() — no pending transcripts. All up to date.")
            return 0

        logger.info(f"run() — {len(pending)} transcript(s) to summarize.")
        saved = 0

        for _, row in pending.iterrows():
            result = self._summarize_one(
                video_id=row["video_id"],
                title=row["title"],
                channel=row["channel"],
                transcript=row["transcript"],
            )
            if result is None:
                continue
            summary_text, model_name = result
            self.db.save_summary(
                video_id=row["video_id"],
                summary=summary_text,
                model_used=model_name,
            )
            saved += 1

        logger.info(f"run() — completed. {saved}/{len(pending)} summaries saved.")
        return saved
