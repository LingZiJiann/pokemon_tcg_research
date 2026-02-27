def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into overlapping character-based chunks.

    YouTube transcripts often lack punctuation, so character-based chunking
    with overlap avoids cutting sentences mid-thought.
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - chunk_overlap

    return chunks
