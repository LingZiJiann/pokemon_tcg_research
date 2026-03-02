from src.youtube_transcripts.youtube_transcript import YouTubeTranscriptCollector
from src.embeddings.vector_store import VectorStore
from src.database.transcript_db import TranscriptDatabase


def main():
    collector = YouTubeTranscriptCollector()
    df = collector.collect()

    db = TranscriptDatabase()
    new_rows = db.save(df)
    print(f"SQLite: {new_rows} new transcript(s) saved.")

    store = VectorStore()
    store.add_from_dataframe(df)
    print(f"Collection size: {store.collection.count()} chunks")

    # Example RAG query
    results = store.query("Charizard market price trend")
    for r in results:
        print(f"\n[{r['metadata']['channel']}] {r['metadata']['title']}")
        print(f"  distance: {r['distance']:.4f}")
        print(f"  chunk {r['metadata']['chunk_index']}/{r['metadata']['total_chunks']}")
        print(f"  {r['text'][:200]}")


if __name__ == "__main__":
    main()
