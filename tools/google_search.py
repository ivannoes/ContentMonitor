"""Google Custom Search tool for the OpenAI agent."""

import json
import sys
from typing import Any

from googleapiclient.discovery import build

from config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from tools.base import BaseTool


class GoogleSearchTool(BaseTool):
    """Wraps the Google Custom Search API as an agent-callable tool."""

    @property
    def name(self) -> str:
        return "google_search"

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": (
                "Search Google for recent news articles using the Google "
                "Custom Search API. Returns a list of results with title, "
                "link, and snippet."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": (
                            "Number of results to return (1-10). Defaults to 5."
                        ),
                    },
                    "date_restrict": {
                        "type": "string",
                        "description": (
                            "Restricts results to a time period. Uses Google's "
                            "dateRestrict format: d[N] for days, w[N] for weeks, "
                            "m[N] for months, y[N] for years. "
                            "Defaults to 'w1' (last week)."
                        ),
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        }

    def execute(self, **kwargs: Any) -> str:
        query: str = kwargs["query"]
        num_results: int = kwargs.get("num_results", 2)
        date_restrict: str = kwargs.get("date_restrict", "w1")

        print(
            f"    \U0001f50d Searching: {query}",
            file=sys.stderr,
            flush=True,
        )

        try:
            service = build(
                "customsearch",
                "v1",
                developerKey=GOOGLE_API_KEY,
                cache_discovery=False,
            )
            response = (
                service.cse()
                .list(q=query, cx=GOOGLE_CSE_ID, dateRestrict=date_restrict, num=num_results)
                .execute()
            )
            items = response.get("items", [])
            results = [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in items
            ]

            # No keyword pre-filter here: every result is passed through so
            # Jev decides relevance later (single consolidated evaluation).
            return json.dumps(results, ensure_ascii=False)
        except Exception as exc:
            print(
                f"    \u26a0 Search error: {exc}",
                file=sys.stderr,
                flush=True,
            )
            return json.dumps({"error": str(exc)})
