from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseAgent(ABC):
    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        system: str,
    ) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        system: str,
    ) -> str:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...
