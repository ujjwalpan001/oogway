from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    llm_provider: Literal["groq", "ollama"] = "groq"

    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    database_url: str = "postgresql+asyncpg://lenny:lenny@localhost:5432/lenny"

    chroma_persist_dir: str = "./chroma_db"
    transcripts_dir: str = "../data/transcripts"

    embedding_model: str = "all-MiniLM-L6-v2"
    retrieval_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 100

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    log_level: str = "INFO"
    app_name: str = "Lenny Growth Assistant"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
