from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector
from src.embeddings.vector_store import VectorStore
from src.database.transcript_db import TranscriptDatabase
from src.summarizer.summarizer import TranscriptSummarizer


def main():
    collector = YouTubeTranscriptCollector()
    df = collector.collect()

    db = TranscriptDatabase()
    new_rows = db.save(df)
    print(f"SQLite: {new_rows} new transcript(s) saved.")

    summarizer = TranscriptSummarizer(db=db)
    summaries_saved = summarizer.run()
    print(f"Summarizer: {summaries_saved} new summary/summaries saved.")

    store = VectorStore()
    store.add_from_dataframe(df)
    print(f"Collection size: {store.collection.count()} chunks")


if __name__ == "__main__":
    main()
