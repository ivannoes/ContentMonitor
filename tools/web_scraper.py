"""Web page scraper tool for the OpenAI agent.

Scrapes web pages (homepages, forum listings, directory pages) to extract
link entries and their surrounding text.  Every entry is passed through
unchanged; relevance filtering is decided later by Jev, not in this tool.

Pages that require authentication, CAPTCHA solving, or that are otherwise
inaccessible are skipped and reported in the output so the agent is always
aware of what could not be reached.
"""

import json
import re
import sys
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import SCRAPE_URLS
from tools.base import BaseTool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_REQUEST_TIMEOUT = 15  # seconds
_MAX_ENTRIES_PER_URL = 200  # safety cap for very large pages

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# HTTP status codes that signal auth / anti-bot challenges
_AUTH_STATUS_CODES = {401, 403, 407}
_CHALLENGE_STATUS_CODES = {429, 503}

# Patterns commonly found in anti-bot / CAPTCHA pages
_CAPTCHA_PATTERNS = re.compile(
    r"(captcha|recaptcha|hcaptcha|cf[-_]?challenge|"
    r"verify.you.are.human|are.you.a.robot|"
    r"access.denied|please.enable.javascript)",
    re.IGNORECASE,
)

# Tags that typically wrap meaningful link entries on listing pages
_ENTRY_TAGS = ["a"]
_CONTAINER_TAGS = ["article", "li", "div", "tr", "section", "h1", "h2", "h3", "h4"]


class WebScraperTool(BaseTool):
    """Scrapes web pages to extract link entries filtered by keywords."""

    # ------------------------------------------------------------------
    # BaseTool interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "scrape_pages"

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": (
                "Scrape one or more web pages (homepages, forum listings, "
                "directory pages) to extract link entries and their "
                "surrounding text. "
                "If no URLs are provided, the default curated list "
                "configured in the application is used. "
                "Returns a JSON object with two keys: 'results' (list of "
                "entries with url, text, and source_page) and 'skipped' "
                "(list of pages that could not be accessed, with the URL "
                "and the reason)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of page URLs to scrape. Each URL "
                            "should point to a homepage, listing page, or "
                            "forum index — not to a single article. "
                            "When omitted the built-in page list is used."
                        ),
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        }

    # ------------------------------------------------------------------
    # Helpers — HTTP fetching
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Return ``True`` if *url* has a valid HTTP(S) scheme and netloc."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    def _fetch_page(self, url: str) -> tuple[str | None, str | None]:
        """Fetch *url* and return ``(html, None)`` on success or
        ``(None, reason)`` when the page must be skipped.
        """
        try:
            resp = requests.get(
                url,
                timeout=_REQUEST_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
                allow_redirects=True,
            )
        except requests.exceptions.SSLError:
            return None, "SSL certificate error"
        except requests.exceptions.ConnectionError:
            return None, "Connection error (DNS or network failure)"
        except requests.exceptions.Timeout:
            return None, f"Request timed out after {_REQUEST_TIMEOUT}s"
        except requests.exceptions.TooManyRedirects:
            return None, "Too many redirects"
        except requests.exceptions.RequestException as exc:
            return None, f"Request error: {exc}"

        # Check for auth-related status codes
        if resp.status_code in _AUTH_STATUS_CODES:
            return None, f"HTTP {resp.status_code} — authentication or access denied"

        # Check for rate-limit / challenge status codes
        if resp.status_code in _CHALLENGE_STATUS_CODES:
            return None, (
                f"HTTP {resp.status_code} — rate-limited or anti-bot challenge"
            )

        # Any other non-2xx response
        if not resp.ok:
            return None, f"HTTP {resp.status_code}"

        # Verify we received HTML content (not PDF, image, etc.)
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return None, f"Non-HTML content type: {content_type}"

        html = resp.text

        # Detect CAPTCHA / anti-bot challenge pages
        if _CAPTCHA_PATTERNS.search(html[:5000]):
            return None, "Page contains a CAPTCHA or anti-bot challenge"

        return html, None

    # ------------------------------------------------------------------
    # Helpers — HTML parsing & entry extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _visible_text(tag: Any) -> str:
        """Extract human-readable text from a BS4 tag, collapsing whitespace."""
        return " ".join(tag.stripped_strings)

    def _extract_entries(self, html: str, base_url: str) -> list[dict]:
        """Parse *html* and return a list of ``{url, text}`` dicts.

        The strategy is to find ``<a>`` tags that carry an ``href`` pointing
        to a distinct page (not anchors, javascript:, mailto:, etc.) and
        collect the surrounding text from the nearest container element.
        """
        soup = BeautifulSoup(html, "html.parser")
        entries: list[dict] = []
        seen_urls: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:")):
                continue

            absolute_url = urljoin(base_url, href)

            # Deduplicate within the same page
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            # Gather context text: look up to the nearest container parent
            context_tag = anchor
            for parent in anchor.parents:
                if parent.name in _CONTAINER_TAGS:
                    context_tag = parent
                    break

            text = self._visible_text(context_tag)
            if not text:
                text = self._visible_text(anchor)

            # Skip entries with very short text (likely nav / icon links)
            if len(text) < 15:
                continue

            entries.append({"url": absolute_url, "text": text})

            if len(entries) >= _MAX_ENTRIES_PER_URL:
                break

        return entries

    # ------------------------------------------------------------------
    # Helpers — entry shaping
    # ------------------------------------------------------------------

    @staticmethod
    def _shape_entries(entries: list[dict], source_url: str) -> list[dict]:
        """Attach the source page and trim long text for every entry.

        No keyword filter is applied here: every entry is passed through so
        Jev decides relevance later in a single consolidated evaluation.
        """
        return [
            {
                "url": entry["url"],
                "text": entry["text"][:500],  # trim long text
                "source_page": source_url,
            }
            for entry in entries
        ]

    # ------------------------------------------------------------------
    # BaseTool.execute
    # ------------------------------------------------------------------

    def execute(self, **kwargs: Any) -> str:
        urls: list[str] = kwargs.get("urls") or list(SCRAPE_URLS)

        results: list[dict] = []
        skipped: list[dict] = []
        total = len(urls)

        for idx, url in enumerate(urls, 1):
            domain = urlparse(url).netloc or url
            print(
                f"    \U0001f310 [{idx}/{total}] Scraping {domain}",
                file=sys.stderr,
                flush=True,
            )

            # Validate URL structure
            if not self._validate_url(url):
                skipped.append({"url": url, "reason": "Invalid URL format"})
                continue

            # Fetch the page
            html, skip_reason = self._fetch_page(url)
            if skip_reason:
                print(
                    f"      \u26a0 Skipped: {skip_reason}",
                    file=sys.stderr,
                    flush=True,
                )
                skipped.append({"url": url, "reason": skip_reason})
                continue

            # Extract and shape entries (no keyword filter here)
            entries = self._extract_entries(html, url)  # type: ignore[arg-type]
            shaped = self._shape_entries(entries, url)
            results.extend(shaped)

        print(
            f"    \U0001f4cb {len(results)} entries kept, {len(skipped)} pages skipped",
            file=sys.stderr,
            flush=True,
        )

        return json.dumps(
            {"results": results, "skipped": skipped},
            ensure_ascii=False,
        )
