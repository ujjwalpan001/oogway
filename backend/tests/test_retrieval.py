"""
Retrieval Unit Tests
Tests the Hybrid Retriever (BM25 + ChromaDB) and RAG citation formatting.
No real database or vector store is needed — ChromaDB is mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.rag.retriever import HybridRetriever, RetrievedChunk
from app.rag.citations import format_context_for_prompt, format_citations_for_display


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(idx: int, guest="Brian Chesky", episode_id="brian-chesky", score=0.8) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{episode_id}__chunk_{idx}",
        text=f"This is chunk {idx} of transcript content about founder-led growth.",
        episode_id=episode_id,
        guest=guest,
        title="Founder Mode",
        youtube_url="https://youtu.be/test",
        publish_date="2024-01-01",
        score=score,
    )


# ---------------------------------------------------------------------------
# Context Formatting Tests
# ---------------------------------------------------------------------------

def test_format_context_no_chunks():
    """format_context_for_prompt should return a 'No relevant' message for empty input."""
    result = format_context_for_prompt([])
    assert "No relevant" in result


def test_format_context_with_chunks():
    """format_context_for_prompt should include guest name, title, and numbered sources."""
    chunks = [make_chunk(0), make_chunk(1)]
    result = format_context_for_prompt(chunks)
    assert "Brian Chesky" in result
    assert "Founder Mode" in result
    assert "Source 1" in result
    assert "Source 2" in result


def test_format_context_preserves_chunk_text():
    """format_context_for_prompt should embed the chunk text in the output."""
    chunks = [make_chunk(0)]
    result = format_context_for_prompt(chunks)
    assert "founder-led growth" in result


# ---------------------------------------------------------------------------
# Citation Formatting Tests
# ---------------------------------------------------------------------------

def test_format_citations_for_display():
    """format_citations_for_display should return a list with correct guest and score."""
    chunks = [make_chunk(0, score=0.95), make_chunk(1, score=0.75)]
    citations = format_citations_for_display(chunks)
    assert len(citations) == 2
    assert citations[0]["guest"] == "Brian Chesky"
    assert citations[0]["relevance_score"] == 95
    assert citations[1]["relevance_score"] == 75


def test_format_citations_truncates_long_text():
    """format_citations_for_display should truncate chunk_text to <=303 chars."""
    long_text = "x" * 500
    chunk = RetrievedChunk(
        chunk_id="test",
        text=long_text,
        episode_id="test",
        guest="Test Guest",
        title="Test Episode",
        youtube_url="",
        publish_date="",
        score=0.5,
    )
    citations = format_citations_for_display([chunk])
    assert len(citations[0]["chunk_text"]) <= 303


def test_format_citations_empty_input():
    """format_citations_for_display should return an empty list for empty input."""
    assert format_citations_for_display([]) == []


def test_format_citations_includes_youtube_url():
    """format_citations_for_display should include the youtube_url in output."""
    chunk = make_chunk(0)
    citations = format_citations_for_display([chunk])
    assert citations[0]["youtube_url"] == "https://youtu.be/test"


# ---------------------------------------------------------------------------
# Hybrid Retriever Tests
# ---------------------------------------------------------------------------

def test_hybrid_retriever_handles_empty_collection():
    """retrieve() should return an empty list when the ChromaDB collection is empty."""
    retriever = HybridRetriever()
    with patch.object(retriever, '_get_collection') as mock_coll:
        mock_coll.return_value.count.return_value = 0
        result = retriever.retrieve("test query")
        assert result == []


def test_rrf_merges_and_deduplicates():
    """_reciprocal_rank_fusion should deduplicate chunks appearing in both result lists."""
    retriever = HybridRetriever()

    chunk_a = ("ep1__chunk_0", 0.9, {"text": "text a", "episode_id": "ep1", "guest": "G1", "title": "T1", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    chunk_b = ("ep1__chunk_0", 0.7, {"text": "text a", "episode_id": "ep1", "guest": "G1", "title": "T1", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    chunk_c = ("ep2__chunk_0", 0.8, {"text": "text c", "episode_id": "ep2", "guest": "G2", "title": "T2", "youtube_url": "", "publish_date": "", "chunk_index": 0})

    result = retriever._reciprocal_rank_fusion([chunk_a, chunk_c], [chunk_b, chunk_c])

    ids = [r.chunk_id for r in result]
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs should not appear in RRF output"
    assert "ep1__chunk_0" in ids


def test_rrf_boosts_chunks_appearing_in_both():
    """Chunks appearing in both semantic and keyword results should rank higher via RRF."""
    retriever = HybridRetriever()
    shared = ("shared__chunk_0", 0.9, {"text": "shared", "episode_id": "shared", "guest": "G", "title": "T", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    only_sem = ("sem__chunk_0", 0.95, {"text": "semantic only", "episode_id": "sem", "guest": "G", "title": "T", "youtube_url": "", "publish_date": "", "chunk_index": 0})

    result = retriever._reciprocal_rank_fusion([shared, only_sem], [shared])
    ids = [r.chunk_id for r in result]
    assert ids.index("shared__chunk_0") < ids.index("sem__chunk_0"), \
        "A chunk in BOTH semantic and keyword results should rank above a semantic-only chunk"


def test_rrf_returns_retrieved_chunk_objects():
    """_reciprocal_rank_fusion should return a list of RetrievedChunk dataclass objects."""
    retriever = HybridRetriever()
    chunk = ("ep1__chunk_0", 0.9, {"text": "text", "episode_id": "ep1", "guest": "G", "title": "T", "youtube_url": "", "publish_date": "", "chunk_index": 0})

    result = retriever._reciprocal_rank_fusion([chunk], [chunk])
    assert len(result) > 0
    assert isinstance(result[0], RetrievedChunk)
    assert result[0].guest == "G"
    assert result[0].text == "text"
