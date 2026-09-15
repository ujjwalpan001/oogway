from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.agent.ollama_agent import OllamaAgent
from app.rag.retriever import retriever
from app.schemas import HealthResponse
from app.config import settings
from app.logging_config import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health():
    checks = {}

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        logger.error("health_db_failed", error=str(exc))

    try:
        count = retriever._get_collection().count()
        checks["chromadb"] = f"ok ({count} chunks indexed)"
    except Exception as exc:
        checks["chromadb"] = f"error: {exc}"

    agent = OllamaAgent()
    try:
        available = await agent.is_available()
        checks["llm"] = "ok" if available else "unavailable (Ollama fallback)"
    except Exception as exc:
        checks["llm"] = f"error: {exc}"

    overall = "ok" if all("error" not in v and "unavailable" not in v for v in checks.values()) else "degraded"

    # Default to claude in health check reporting, since it's the primary now
    return HealthResponse(
        status=overall,
        version=settings.app_version,
        provider="claude",
        model="claude-3-5-sonnet-20240620",
        checks=checks,
    )
