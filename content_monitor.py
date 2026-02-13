"""Content Monitor -- entry point.

Deterministically executes all three data-collection tools (RSS feeds,
Google search, web scraping), writes the combined results to a CSV file,
then sends the CSV content to the OpenAI model for summarization.
"""

import csv
import io
import json
import sys
from datetime import datetime

from agent import ContentAgent
from config import (
    GOOGLE_SEARCH_KEYWORDS,
    PRIMARY_KEYWORDS,
    REGION_KEYWORDS,
    SECONDARY_KEYWORDS,
    validate_google_credentials,
    validate_openai_credentials,
)
from tools.feed_reader import FeedReaderTool
from tools.google_search import GoogleSearchTool
from tools.web_scraper import WebScraperTool

# ------------------------------------------------------------------
# CSV output path
# ------------------------------------------------------------------
CSV_PATH = "monitor_results.csv"
CSV_COLUMNS = [
    "date",
    "url",
    "title",
    "summary",
    "source",
    "matched_keywords",
    "tool",
]

# ------------------------------------------------------------------
# System-level instructions sent to the model for summarization
# ------------------------------------------------------------------
SUMMARY_INSTRUCTIONS = """\
You are an anti-piracy content monitoring assistant.

You will receive the contents of a CSV file with articles collected from
RSS feeds, Google searches, and scraped web pages.  Every article has
already been pre-filtered through keyword and region filters.
Apply a second pass: discard any article that is NOT relevant to the
keyword and region criteria listed below.

REGION keywords (article MUST mention at least one):
  {region_keywords}

PRIMARY keywords (preferred):
  {primary_keywords}

SECONDARY keywords (supporting):
  {secondary_keywords}

Your job is to:
  1.  Remove duplicate articles (same URL or same headline).
  2.  Discard any article whose title and summary do not mention at least
      one REGION keyword.
  3.  Return a **numbered list** of the remaining articles with:
      - Title
      - URL
      - Publication date (if available)
      - Source
      - A one-line summary
  4.  At the end, print a short summary line:
      "Total relevant articles found: <N>"
"""


def _build_summary_instructions() -> str:
    """Build the summarization prompt with the configured keyword lists."""
    return SUMMARY_INSTRUCTIONS.format(
        region_keywords=", ".join(REGION_KEYWORDS),
        primary_keywords=", ".join(PRIMARY_KEYWORDS),
        secondary_keywords=", ".join(SECONDARY_KEYWORDS),
    )


# ------------------------------------------------------------------
# Data collection
# ------------------------------------------------------------------

def _collect_feeds() -> list[dict]:
    """Run the feed reader and normalise results."""
    print(
        "\n\U0001f4e1 Step 1/3: Reading RSS feeds...",
        file=sys.stderr,
        flush=True,
    )
    tool = FeedReaderTool()
    raw = json.loads(tool.execute())
    rows: list[dict] = []
    for item in raw:
        rows.append(
            {
                "date": item.get("date", ""),
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "matched_keywords": ", ".join(
                    item.get("matched_keywords", [])
                ),
                "tool": "read_feeds",
            }
        )
    print(
        f"  \u2705 {len(rows)} articles from feeds",
        file=sys.stderr,
        flush=True,
    )
    return rows


def _collect_google() -> list[dict]:
    """Run Google searches for every configured keyword."""
    print(
        "\n\U0001f50d Step 2/3: Running Google searches...",
        file=sys.stderr,
        flush=True,
    )
    tool = GoogleSearchTool()
    rows: list[dict] = []
    for keyword in GOOGLE_SEARCH_KEYWORDS:
        raw = json.loads(tool.execute(query=keyword))
        if isinstance(raw, dict) and "error" in raw:
            print(
                f"  \u26a0 Error for '{keyword}': {raw['error']}",
                file=sys.stderr,
                flush=True,
            )
            continue
        for item in raw:
            rows.append(
                {
                    "date": "",
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "summary": item.get("snippet", ""),
                    "source": "Google Search",
                    "matched_keywords": ", ".join(
                        item.get("matched_keywords", [])
                    ),
                    "tool": "google_search",
                }
            )
    print(
        f"  \u2705 {len(rows)} results from Google",
        file=sys.stderr,
        flush=True,
    )
    return rows


def _collect_scrapes() -> list[dict]:
    """Run the web scraper on the default page list."""
    print(
        "\n\U0001f310 Step 3/3: Scraping web pages...",
        file=sys.stderr,
        flush=True,
    )
    tool = WebScraperTool()
    raw = json.loads(tool.execute())
    results = raw.get("results", [])
    skipped = raw.get("skipped", [])

    rows: list[dict] = []
    for item in results:
        rows.append(
            {
                "date": "",
                "url": item.get("url", ""),
                "title": "",
                "summary": item.get("text", ""),
                "source": item.get("source_page", ""),
                "matched_keywords": ", ".join(
                    item.get("matched_keywords", [])
                ),
                "tool": "scrape_pages",
            }
        )

    if skipped:
        for s in skipped:
            print(
                f"  \u26a0 Skipped {s['url']}: {s['reason']}",
                file=sys.stderr,
                flush=True,
            )

    print(
        f"  \u2705 {len(rows)} entries from scraping"
        f" ({len(skipped)} pages skipped)",
        file=sys.stderr,
        flush=True,
    )
    return rows


# ------------------------------------------------------------------
# CSV helpers
# ------------------------------------------------------------------

def _write_csv(rows: list[dict], path: str) -> None:
    """Write *rows* to a CSV file at *path*."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv_as_text(path: str) -> str:
    """Read the CSV file at *path* and return it as a string."""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------------------------
# De-duplicate by URL before writing
# ------------------------------------------------------------------

def _deduplicate(rows: list[dict]) -> list[dict]:
    """Remove entries with duplicate URLs, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[dict] = []
    for row in rows:
        url = row.get("url", "")
        if url and url in seen:
            continue
        seen.add(url)
        unique.append(row)
    return unique


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    validate_google_credentials()
    validate_openai_credentials()

    # 1. Collect data deterministically from all three sources
    all_rows: list[dict] = []
    all_rows.extend(_collect_feeds())
    all_rows.extend(_collect_google())
    all_rows.extend(_collect_scrapes())

    # 2. De-duplicate and write to CSV
    unique_rows = _deduplicate(all_rows)
    _write_csv(unique_rows, CSV_PATH)
    print(
        f"\n\U0001f4be {len(unique_rows)} unique entries written to {CSV_PATH}"
        f" ({len(all_rows) - len(unique_rows)} duplicates removed)",
        file=sys.stderr,
        flush=True,
    )

    # 3. Send CSV content to the model for summarization
    csv_text = _read_csv_as_text(CSV_PATH)
    instructions = _build_summary_instructions()
    agent = ContentAgent()
    answer = agent.summarize(csv_text, instructions=instructions)

    print(answer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
