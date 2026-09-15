import asyncio
from typing import AsyncIterator
from anthropic import AsyncAnthropic
from app.agent.base import BaseAgent
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

class ClaudeAgent(BaseAgent):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        # Initialize lazily to avoid errors if API key is invalid
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        if not self.client:
            raise ValueError("Claude API key not configured")
            
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                system=system,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as exc:
            logger.error("claude_stream_failed", model=self.model, error=str(exc))
            raise

    async def complete(self, messages: list[dict], system: str) -> str:
        if not self.client:
            raise ValueError("Claude API key not configured")
            
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                system=system,
                messages=messages
            )
            return response.content[0].text
        except Exception as exc:
            logger.error("claude_complete_failed", model=self.model, error=str(exc))
            raise

    async def is_available(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": "ping"}]
            )
            return True
        except Exception:
            return False
