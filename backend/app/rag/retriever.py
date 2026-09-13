from dataclasses import dataclass
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    episode_id: str
    guest: str
    title: str
    youtube_url: str
    publish_date: str
    score: float


class HybridRetriever:
    def __init__(self):
        self._collection = None
        self._model = None
        self._bm25 = None
        self._bm25_corpus: list[str] = []
        self._bm25_metas: list[dict] = []

    def _get_collection(self):
        if self._collection is None:
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self._collection = client.get_or_create_collection("lenny_transcripts")
        return self._collection

    def _get_model(self):
        if self._model is None:
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model

    def _ensure_bm25(self):
        if self._bm25 is not None:
            return
        collection = self._get_collection()
        result = collection.get(include=["documents", "metadatas"])
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []

        if not docs:
            logger.warning("bm25_build_skipped_no_docs")
            return

        self._bm25_corpus = docs
        self._bm25_metas = metas
        tokenized = [d.lower().split() for d in docs]
        self._bm25 = BM25Okapi(tokenized)
        logger.info("bm25_index_built", doc_count=len(docs))

    def _semantic_search(self, query: str, top_k: int) -> list[tuple[str, float, dict]]:
        model = self._get_model()
        collection = self._get_collection()
        embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )
        items = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunk_id = f"{meta.get('episode_id')}__chunk_{meta.get('chunk_index', 0)}"
            score = 1.0 - float(dist)
            items.append((chunk_id, score, {"text": doc, **meta}))
        return items

    def _bm25_search(self, query: str, top_k: int) -> list[tuple[str, float, dict]]:
        self._ensure_bm25()
        if self._bm25 is None:
            return []
        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)
        indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        items = []
        for idx in indices:
            meta = self._bm25_metas[idx]
            doc = self._bm25_corpus[idx]
            chunk_id = f"{meta.get('episode_id')}__chunk_{meta.get('chunk_index', 0)}"
            items.append((chunk_id, float(scores[idx]), {"text": doc, **meta}))
        return items

    def _reciprocal_rank_fusion(
        self,
        semantic: list[tuple[str, float, dict]],
        keyword: list[tuple[str, float, dict]],
        k: int = 60,
    ) -> list[RetrievedChunk]:
        scores: dict[str, float] = {}
        data: dict[str, dict] = {}

        for rank, (chunk_id, _, meta) in enumerate(semantic):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
            data[chunk_id] = meta

        for rank, (chunk_id, _, meta) in enumerate(keyword):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
            data.setdefault(chunk_id, meta)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        chunks = []
        for chunk_id, score in ranked[: settings.retrieval_top_k]:
            meta = data[chunk_id]
            chunks.append(RetrievedChunk(
                chunk_id=chunk_id,
                text=meta.get("text", ""),
                episode_id=meta.get("episode_id", ""),
                guest=meta.get("guest", ""),
                title=meta.get("title", ""),
                youtube_url=meta.get("youtube_url", ""),
                publish_date=meta.get("publish_date", ""),
                score=score,
            ))
        return chunks

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        try:
            if (self._get_collection().count() or 0) == 0:
                logger.warning("collection_empty_returning_no_results")
                return []

            semantic = self._semantic_search(query, top_k=10)
            keyword = self._bm25_search(query, top_k=10)
            chunks = self._reciprocal_rank_fusion(semantic, keyword)
            logger.info("retrieval_complete", query_len=len(query), chunks_returned=len(chunks))
            return chunks
        except Exception as exc:
            logger.error("retrieval_failed", error=str(exc))
            return []


retriever = HybridRetriever()
