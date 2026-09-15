from app.agent.base import BaseAgent
from app.agent.claude_agent import ClaudeAgent
from app.agent.ollama_agent import OllamaAgent
from app.models import User
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

def get_agent(user: User, provider: str = None, model: str = None) -> BaseAgent:
    provider = provider or settings.llm_provider
    
    if provider == "claude":
        # Check if Claude is available and user has a key
        if user.claude_api_key:
            return ClaudeAgent(api_key=user.claude_api_key, model=model or settings.claude_model)
        else:
            logger.warning("missing_claude_key_falling_back_to_ollama", user_id=user.id)
            return OllamaAgent()
    elif provider == "openai":
        # Placeholder for OpenAIAgent
        raise NotImplementedError("OpenAI agent not yet implemented")
    else:
        return OllamaAgent()
