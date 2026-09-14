import pytest
from unittest.mock import MagicMock, patch
from app.rag.retriever import HybridRetriever, RetrievedChunk
from app.rag.citations import format_context_for_prompt, format_citations_for_display


def make_chunk(idx: int, guest="Brian Chesky", score=0.8) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"brian-chesky__chunk_{idx}",
        text=f"This is chunk {idx} of transcript content about founder-led growth.",
        episode_id="brian-chesky",
        guest=guest,
        title="Founder Mode",
        youtube_url="https://youtu.be/test",
        publish_date="2024-01-01",
        score=score,
    )


def test_format_context_no_chunks():
    result = format_context_for_prompt([])
    assert "No relevant" in result


def test_format_context_with_chunks():
    chunks = [make_chunk(0), make_chunk(1)]
    result = format_context_for_prompt(chunks)
    assert "Brian Chesky" in result
    assert "Founder Mode" in result
    assert "Source 1" in result
    assert "Source 2" in result


def test_format_citations_for_display():
    chunks = [make_chunk(0, score=0.95), make_chunk(1, score=0.75)]
    citations = format_citations_for_display(chunks)
    assert len(citations) == 2
    assert citations[0]["guest"] == "Brian Chesky"
    assert citations[0]["relevance_score"] == 95
    assert citations[1]["relevance_score"] == 75


def test_format_citations_truncates_long_text():
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


def test_hybrid_retriever_handles_empty_collection():
    retriever = HybridRetriever()
    with patch.object(retriever, '_get_collection') as mock_coll:
        mock_coll.return_value.count.return_value = 0
        result = retriever.retrieve("test query")
        assert result == []


def test_rrf_merges_and_deduplicates():
    retriever = HybridRetriever()

    chunk_a = ("ep1__chunk_0", 0.9, {"text": "text a", "episode_id": "ep1", "guest": "G1", "title": "T1", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    chunk_b = ("ep1__chunk_0", 0.7, {"text": "text a", "episode_id": "ep1", "guest": "G1", "title": "T1", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    chunk_c = ("ep2__chunk_0", 0.8, {"text": "text c", "episode_id": "ep2", "guest": "G2", "title": "T2", "youtube_url": "", "publish_date": "", "chunk_index": 0})

    result = retriever._reciprocal_rank_fusion([chunk_a, chunk_c], [chunk_b, chunk_c])

    ids = [r.chunk_id for r in result]
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs in RRF output"
    assert "ep1__chunk_0" in ids


def test_rrf_boosts_chunks_appearing_in_both():
    retriever = HybridRetriever()
    shared = ("shared__chunk_0", 0.9, {"text": "shared", "episode_id": "shared", "guest": "G", "title": "T", "youtube_url": "", "publish_date": "", "chunk_index": 0})
    only_sem = ("sem__chunk_0", 0.95, {"text": "semantic only", "episode_id": "sem", "guest": "G", "title": "T", "youtube_url": "", "publish_date": "", "chunk_index": 0})

    result = retriever._reciprocal_rank_fusion([shared, only_sem], [shared])
    ids = [r.chunk_id for r in result]
    assert ids.index("shared__chunk_0") < ids.index("sem__chunk_0"), "Shared chunk should rank above semantic-only"
