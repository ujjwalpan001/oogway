import os
import re
import frontmatter
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def load_transcripts(transcripts_dir: str) -> list[dict]:
    episodes = []
    if not os.path.exists(transcripts_dir):
        logger.warning("transcripts_dir_not_found", path=transcripts_dir)
        return episodes

    for guest_folder in os.listdir(transcripts_dir):
        transcript_path = os.path.join(transcripts_dir, guest_folder, "transcript.md")
        if not os.path.exists(transcript_path):
            continue
        try:
            post = frontmatter.load(transcript_path)
            meta = dict(post.metadata)
            episodes.append({
                "guest": str(meta.get("guest", guest_folder)),
                "title": str(meta.get("title", "")),
                "youtube_url": str(meta.get("youtube_url", "")),
                "publish_date": str(meta.get("publish_date", "")),
                "description": str(meta.get("description", "")),
                "episode_id": guest_folder,
                "content": post.content,
            })
        except Exception as exc:
            logger.warning("transcript_parse_failed", path=transcript_path, error=str(exc))

    logger.info("transcripts_loaded", count=len(episodes))
    return episodes


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest_transcripts():
    transcripts_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", settings.transcripts_dir)
    )
    episodes = load_transcripts(transcripts_dir)
    if not episodes:
        logger.error("no_transcripts_found", dir=transcripts_dir)
        return

    model = SentenceTransformer(settings.embedding_model)

    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(
        name="lenny_transcripts",
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids = set(collection.get(include=[])["ids"])
    logger.info("existing_chunks_in_db", count=len(existing_ids))

    new_docs, new_embeddings, new_metadatas, new_ids = [], [], [], []

    for ep in episodes:
        chunks = chunk_text(ep["content"], settings.chunk_size, settings.chunk_overlap)
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{ep['episode_id']}__chunk_{idx}"
            if chunk_id in existing_ids:
                continue

            embedding = model.encode(chunk, show_progress_bar=False).tolist()
            new_docs.append(chunk)
            new_embeddings.append(embedding)
            new_ids.append(chunk_id)
            new_metadatas.append({
                "episode_id": ep["episode_id"],
                "guest": ep["guest"],
                "title": ep["title"],
                "youtube_url": ep["youtube_url"],
                "publish_date": ep["publish_date"],
                "chunk_index": idx,
            })

    if new_docs:
        batch_size = 100
        for i in range(0, len(new_docs), batch_size):
            collection.add(
                documents=new_docs[i:i+batch_size],
                embeddings=new_embeddings[i:i+batch_size],
                ids=new_ids[i:i+batch_size],
                metadatas=new_metadatas[i:i+batch_size],
            )
        logger.info("chunks_ingested", count=len(new_docs))
    else:
        logger.info("no_new_chunks_to_ingest")


if __name__ == "__main__":
    ingest_transcripts()
