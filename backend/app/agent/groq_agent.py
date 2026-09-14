from typing import AsyncIterator
from groq import AsyncGroq
from app.agent.base import BaseAgent
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class GroqAgent(BaseAgent):
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system}] + messages
        try:
            async with self.client.chat.completions.stream(
                model=self.model,
                messages=full_messages,
                max_tokens=4096,
                temperature=0.7,
            ) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        except Exception as exc:
            logger.error("groq_stream_failed", model=self.model, error=str(exc))
            raise

    async def complete(self, messages: list[dict], system: str) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=4096,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("groq_complete_failed", model=self.model, error=str(exc))
            raise

    async def is_available(self) -> bool:
        if not settings.groq_api_key:
            return False
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
