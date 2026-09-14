from app.agent.base import BaseAgent
from app.agent.groq_agent import GroqAgent
from app.agent.ollama_agent import OllamaAgent
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_agent: BaseAgent | None = None


def get_agent() -> BaseAgent:
    global _agent
    if _agent is None:
        if settings.llm_provider == "groq":
            _agent = GroqAgent()
            logger.info("agent_initialized", provider="groq", model=settings.groq_model)
        else:
            _agent = OllamaAgent()
            logger.info("agent_initialized", provider="ollama", model=settings.ollama_model)
    return _agent


def reset_agent():
    global _agent
    _agent = None
