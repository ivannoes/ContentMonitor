from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Every tool must provide its OpenAI schema and an execute method."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name matching the function schema ``name`` field."""

    @property
    @abstractmethod
    def schema(self) -> dict:
        """Return the OpenAI function-tool definition (Responses API format).

        Expected shape::

            {
                "type": "function",
                "name": "<tool_name>",
                "description": "...",
                "parameters": { ... }
            }
        """

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Run the tool logic and return a JSON-serialisable string result."""
