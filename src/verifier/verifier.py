"""Verification agent for Pokemon TCG summaries.

For each AI-generated summary, this agent:
1. Extracts card names and claimed prices using Claude.
2. Searches Tavily for current market prices and eBay last-sold listings.
3. Stores a structured verification report in the ``verifications`` table.
4. Feeds the verification data back to Claude to produce buy recommendations
   (feedback loop), stored as ``buy_recommendations`` in the ``summaries`` table.
"""

import json

import anthropic
from tavily import TavilyClient

from config.config import settings
from src.database.transcript_db import TranscriptDatabase
from src.utils.logger import get_logger

logger = get_logger("verifier")

_EXTRACT_CARDS_PROMPT = """\
Extract all Pokemon TCG cards mentioned in the summary below along with any \
prices claimed for them.

Return ONLY a JSON array of objects with two keys:
  "card_name"     — the card's full name (e.g. "Charizard ex", "Umbreon VMAX")
  "claimed_price" — the price mentioned, or null if none

SUMMARY:
{summary}

JSON ARRAY:"""

_BUY_RECOMMENDATION_PROMPT = """\
You are an expert Pokemon TCG market analyst. A YouTube video summary and \
real-world verification data (web searches and eBay last-sold listings) are \
provided below.

Produce buy recommendations:

1. **Per-card verdicts** — For each card mentioned, output:
   - Card name
   - **Buy** or **Skip** verdict
   - Short justification comparing the video's claimed price against verified \
market data (is it undervalued, overpriced, or fairly priced?)

2. **Top Picks (ranked)** — End with a ranked list of the best cards to buy, \
ordered by value opportunity. Include a brief reason for each pick.

Consider: price accuracy from the video, current market trends, recent sold \
prices, and potential upside.

INITIAL SUMMARY:
{summary}

VERIFICATION DATA:
{report}

BUY RECOMMENDATIONS:"""


class TranscriptVerifier:
    """Verify AI summaries against real-world market data and refine them.

    Usage:
        verifier = TranscriptVerifier()
        n = verifier.run()
        print(f"Verified {n} summary/summaries.")
    """

    def __init__(self, db: TranscriptDatabase | None = None) -> None:
        self.db = db if db is not None else TranscriptDatabase()
        self._claude: anthropic.Anthropic | None = None
        self._tavily: TavilyClient | None = None

    def _get_claude(self) -> anthropic.Anthropic:
        if self._claude is None:
            self._claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._claude

    def _get_tavily(self) -> TavilyClient:
        if self._tavily is None:
            self._tavily = TavilyClient(api_key=settings.tavily_api_key)
        return self._tavily

    # ------------------------------------------------------------------
    # Card extraction
    # ------------------------------------------------------------------

    def _extract_cards(self, summary: str) -> list[dict]:
        """Ask Claude to return a JSON list of {card_name, claimed_price}."""
        prompt = _EXTRACT_CARDS_PROMPT.format(summary=summary)
        response = self._get_claude().messages.create(
            model=settings.claude_model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        cards = json.loads(text)
        return cards[: settings.max_cards_per_verification]

    # ------------------------------------------------------------------
    # Tavily searches
    # ------------------------------------------------------------------

    def _search_card_prices(self, card_name: str) -> tuple[list[dict], list[str]]:
        """Run general market + eBay sold searches for one card.

        Returns (result_snippets, source_urls).
        """
        tavily = self._get_tavily()
        results: list[dict] = []
        sources: list[str] = []

        for query in (
            f"{card_name} pokemon tcg card price",
            f"{card_name} pokemon card sold completed site:ebay.com",
        ):
            response = tavily.search(
                query=query,
                search_depth=settings.verification_search_depth,
                max_results=3,
            )
            for r in response.get("results", []):
                results.append(
                    {
                        "card": card_name,
                        "title": r.get("title", ""),
                        "content": r.get("content", "")[:300],
                    }
                )
                url = r.get("url", "")
                if url:
                    sources.append(url)

        return results, sources

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def _verify_summary(self, summary: str) -> dict:
        """Extract cards, search prices, return verification payload."""
        try:
            cards = self._extract_cards(summary)
        except Exception as exc:
            logger.warning(f"_verify_summary() — card extraction failed: {exc}")
            cards = []

        if not cards:
            return {
                "price_data": {},
                "sources": [],
                "report": "No cards identified for verification.",
            }

        all_results: list[dict] = []
        all_sources: list[str] = []
        price_data: dict[str, str] = {}

        for card_info in cards:
            card_name = (card_info.get("card_name") or "").strip()
            if not card_name:
                continue
            try:
                snippets, sources = self._search_card_prices(card_name)
                all_results.extend(snippets)
                all_sources.extend(sources)
                if snippets:
                    price_data[card_name] = " | ".join(
                        s["content"] for s in snippets[:2]
                    )
            except Exception as exc:
                logger.warning(
                    f"_verify_summary() — price search failed for '{card_name}': {exc}"
                )

        # Build markdown report
        report_lines = ["## Price Verification\n"]
        if price_data:
            for card_name, info in price_data.items():
                report_lines += [f"### {card_name}", info, ""]
        else:
            report_lines.append("No price data found.")

        return {
            "price_data": price_data,
            "sources": list(
                dict.fromkeys(all_sources)
            ),  # deduplicated, order-preserving
            "report": "\n".join(report_lines),
        }

    # ------------------------------------------------------------------
    # Feedback loop — buy recommendations
    # ------------------------------------------------------------------

    def _generate_buy_recommendations(
        self, initial_summary: str, verification: dict
    ) -> str:
        """Re-prompt Claude with the initial summary + verification data to produce buy recommendations."""
        prompt = _BUY_RECOMMENDATION_PROMPT.format(
            summary=initial_summary,
            report=verification["report"],
        )
        try:
            response = self._get_claude().messages.create(
                model=settings.claude_model,
                max_tokens=settings.summary_max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as exc:
            logger.warning(
                f"_generate_buy_recommendations() — Claude failed: {exc}. Returning empty recommendations."
            )
            return "No buy recommendations could be generated."

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> int:
        """Verify all unverified summaries and store refined summaries.

        Idempotent: skips videos already in the verifications table.
        Returns the number of summaries successfully verified in this run.
        """
        if not settings.tavily_api_key:
            logger.warning(
                "run() — TAVILY_API_KEY not set. Skipping verification stage."
            )
            return 0

        pending = self.db.get_unverified_summaries()
        if pending.empty:
            logger.info("run() — no pending summaries to verify. All up to date.")
            return 0

        logger.info(f"run() — {len(pending)} summary/summaries to verify.")
        verified = 0

        for _, row in pending.iterrows():
            video_id = row["video_id"]
            try:
                verification = self._verify_summary(row["summary"])
                self.db.save_verification(
                    video_id=video_id,
                    verification_report=verification["report"],
                    sources=json.dumps(verification["sources"]),
                    price_data=json.dumps(verification["price_data"]),
                    model_used=settings.claude_model,
                )
                recommendations = self._generate_buy_recommendations(
                    initial_summary=row["summary"],
                    verification=verification,
                )
                self.db.save_buy_recommendations(
                    video_id=video_id, recommendations=recommendations
                )
                verified += 1
                logger.info(
                    f"run() — verified and generated buy recommendations for {video_id}."
                )
            except Exception as exc:
                logger.error(
                    f"run() — failed for {video_id}: {type(exc).__name__}: {exc}. Skipping."
                )

        logger.info(f"run() — completed. {verified}/{len(pending)} summaries verified.")
        return verified
