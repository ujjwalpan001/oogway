"""
Run this once to ingest all transcripts into ChromaDB.
Usage: python scripts/ingest.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag.ingestion import ingest_transcripts
from app.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("ingest")

if __name__ == "__main__":
    logger.info("ingestion_started")
    ingest_transcripts()
    logger.info("ingestion_complete")
