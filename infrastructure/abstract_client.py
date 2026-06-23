from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class TruncationException(Exception):
    """Raised when the LLM exhausts its token budget before completing the JSON output."""
    pass

class RefusalException(Exception):
    """Raised when the LLM's safety filters decline to process the prompt."""
    pass

class StructuredLLMClient(ABC):
    """Port interface for the infrastructure layer."""

    @abstractmethod
    async def raw_extract(
        self,
        schema: Type[T],
        system_instruction: str,
        user_content: str,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Extract a raw, unvalidated dictionary from the LLM matching schema."""
        pass