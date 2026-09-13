from app.rag.retriever import RetrievedChunk


def format_context_for_prompt(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant transcript excerpts found."

    lines = []
    for i, chunk in enumerate(chunks, 1):
        source = f"{chunk.guest} — \"{chunk.title}\""
        if chunk.youtube_url:
            source += f" ({chunk.youtube_url})"
        lines.append(f"[Source {i}: {source}]\n{chunk.text.strip()}\n")

    return "\n---\n".join(lines)


def format_citations_for_display(chunks: list[RetrievedChunk]) -> list[dict]:
    return [
        {
            "episode_id": c.chunk_id,
            "guest": c.guest,
            "episode_title": c.title,
            "chunk_text": c.text[:300] + "..." if len(c.text) > 300 else c.text,
            "youtube_url": c.youtube_url,
            "relevance_score": int(c.score * 100),
        }
        for c in chunks
    ]
