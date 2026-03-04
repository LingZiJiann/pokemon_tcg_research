from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector
from src.database.transcript_db import TranscriptDatabase
from src.summarizer.summarizer import TranscriptSummarizer
from src.verifier.verifier import TranscriptVerifier


def main():
    collector = YouTubeTranscriptCollector()
    df = collector.collect()

    db = TranscriptDatabase()
    new_rows = db.save(df)
    print(f"SQLite: {new_rows} new transcript(s) saved.")

    summarizer = TranscriptSummarizer(db=db)
    summaries_saved = summarizer.run()
    print(f"Summarizer: {summaries_saved} new summary/summaries saved.")

    verifier = TranscriptVerifier(db=db)
    verified = verifier.run()
    print(f"Verifier: {verified} summary/summaries verified and refined.")


if __name__ == "__main__":
    main()
