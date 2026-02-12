"""RSS / Atom feed reader tool for the OpenAI agent."""

import json
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests

from config import RSS_FEEDS
from tools.base import BaseTool


class FeedReaderTool(BaseTool):
    """Fetches and parses RSS/Atom feeds, returning article entries."""

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    @property
    def name(self) -> str:
        return "read_feeds"

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": (
                "Read and parse one or more RSS/Atom feeds. "
                "If no feed URLs are provided, the default curated list "
                "configured in the application is used. "
                "Returns a JSON array of articles with title, link, summary, "
                "source, and publication date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feed_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of RSS/Atom feed URLs to read. "
                            "When omitted the built-in feed list is used."
                        ),
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Check whether *url* has a valid scheme and netloc."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def _is_feed_accessible(self, feed_url: str, timeout: int = 10) -> bool:
        """Return ``True`` if the feed responds with HTTP 200."""
        try:
            headers = {"User-Agent": self._USER_AGENT}
            resp = requests.get(feed_url, timeout=timeout, headers=headers)
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _extract_date(entry: Any) -> str:
        """Best-effort extraction of a publication date string."""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d")
        except Exception:
            pass
        return ""

    def _parse_feed(self, feed_url: str) -> list[dict]:
        """Parse a single feed and return a list of article dicts."""
        articles: list[dict] = []
        try:
            feed = feedparser.parse(feed_url)

            if hasattr(feed, "status") and feed.status != 200:
                return articles

            if not hasattr(feed, "entries") or not feed.entries:
                return articles

            for entry in feed.entries:
                try:
                    title = getattr(entry, "title", "") or ""
                    summary = getattr(entry, "summary", "") or ""
                    articles.append(
                        {
                            "date": self._extract_date(entry),
                            "url": getattr(entry, "link", ""),
                            "title": title,
                            "summary": summary,
                            "source": feed_url,
                        }
                    )
                except Exception:
                    continue
        except Exception:
            pass
        return articles

    # ------------------------------------------------------------------
    # BaseTool interface
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> str:
        feed_urls: list[str] = kwargs.get("feed_urls") or list(RSS_FEEDS)

        valid_feeds = [url for url in feed_urls if self._validate_url(url)]
        all_articles: list[dict] = []

        for url in valid_feeds:
            all_articles.extend(self._parse_feed(url))

        return json.dumps(all_articles, ensure_ascii=False)
