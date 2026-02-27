import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

from config.config import settings
from src.embeddings.chunker import chunk_text
from src.utils.logger import get_logger

logger = get_logger("vector_db")


class VectorStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.vector_db_path)
        self.model = SentenceTransformer(settings.embedding_model)
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStore ready — collection '{settings.collection_name}' "
            f"has {self.collection.count()} documents"
        )

    def _already_stored(self, video_id: str) -> bool:
        """Check whether any chunks for a video are already in the collection.

        Args:
            video_id: YouTube video ID to look up.

        Returns:
            True if at least one chunk exists for the video, False otherwise.
        """
        results = self.collection.get(where={"video_id": video_id}, limit=1)
        return len(results["ids"]) > 0

    def add_from_dataframe(self, df: pd.DataFrame) -> None:
        """Chunk, embed, and upsert all available transcripts from a DataFrame.

        Skips videos already present in the collection (idempotent).

        Args:
            df: DataFrame with columns including ``video_id``, ``title``,
                ``transcript``, ``transcript_available``, ``channel``,
                ``channel_id``, ``published_at``, and ``url``.
        """
        available = df[df["transcript_available"]]
        if available.empty:
            logger.warning("No transcripts available to embed.")
            return

        for _, row in available.iterrows():
            video_id = row["video_id"]

            if self._already_stored(video_id):
                logger.info(f"Skipping '{row['title']}' — already in store.")
                continue

            chunks = chunk_text(
                row["transcript"], settings.chunk_size, settings.chunk_overlap
            )
            if not chunks:
                logger.warning(f"No chunks produced for video {video_id}.")
                continue

            embeddings = self.model.encode(chunks, show_progress_bar=False).tolist()

            self.collection.add(
                ids=[f"{video_id}_chunk_{i}" for i in range(len(chunks))],
                documents=chunks,
                embeddings=embeddings,
                metadatas=[
                    {
                        "channel": row["channel"],
                        "channel_id": row["channel_id"],
                        "video_id": video_id,
                        "title": row["title"],
                        "published_at": row["published_at"],
                        "url": row["url"],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                    for i in range(len(chunks))
                ],
            )
            logger.info(f"Stored {len(chunks)} chunks for '{row['title']}'.")

    def query(
        self,
        text: str,
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        """Return the top-n most relevant chunks for a query string.

        Args:
            text: Natural-language query.
            n_results: Number of chunks to retrieve.
            where: Optional ChromaDB metadata filter (e.g. {"channel": "TwicebakedJake"}).

        Returns:
            List of dicts with keys: text, metadata, distance.
        """
        query_embedding = self.model.encode([text]).tolist()

        kwargs: dict = {"query_embeddings": query_embedding, "n_results": n_results}
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        return [
            {
                "text": doc,
                "metadata": meta,
                "distance": dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
