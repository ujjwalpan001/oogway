from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.agent.router import get_agent
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

    agent = get_agent()
    try:
        available = await agent.is_available()
        checks["llm"] = "ok" if available else "unavailable"
    except Exception as exc:
        checks["llm"] = f"error: {exc}"

    overall = "ok" if all("error" not in v and "unavailable" not in v for v in checks.values()) else "degraded"

    model = settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model
    return HealthResponse(
        status=overall,
        version=settings.app_version,
        provider=settings.llm_provider,
        model=model,
        checks=checks,
    )
