from typing import AsyncIterator
import httpx
from app.agent.base import BaseAgent
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

TIMEOUT = 120.0


class OllamaAgent(BaseAgent):
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def _build_prompt(self, messages: list[dict], system: str) -> str:
        parts = [f"<|system|>\n{system}\n"]
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            parts.append(f"<|{role}|>\n{msg['content']}\n")
        parts.append("<|assistant|>\n")
        return "".join(parts)

    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        prompt = self._build_prompt(messages, system)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    import json
                    async for line in resp.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield token
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            logger.error("ollama_not_reachable", url=self.base_url)
            raise RuntimeError(f"Ollama is not running at {self.base_url}. Start it with: ollama serve")
        except Exception as exc:
            logger.error("ollama_stream_failed", model=self.model, error=str(exc))
            raise

    async def complete(self, messages: list[dict], system: str) -> str:
        result = []
        async for token in self.stream(messages, system):
            result.append(token)
        return "".join(result)

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
