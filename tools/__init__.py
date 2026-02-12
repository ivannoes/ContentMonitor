"""Tool registry for OpenAI function-calling integration.

To add a new tool:
  1. Create a class that inherits from ``BaseTool`` in a new module under
     ``tools/``.
  2. Import and append an instance to the ``TOOL_REGISTRY`` list below.

The agent discovers available tools automatically through this registry.
"""

from tools.google_search import GoogleSearchTool
from tools.feed_reader import FeedReaderTool

# ------------------------------------------------------------------
# Central registry – add new tool instances here.
# ------------------------------------------------------------------
TOOL_REGISTRY: list = [
    GoogleSearchTool(),
    FeedReaderTool(),
]
