"""Content Monitor -- entry point.

Deterministically executes all three data-collection tools (RSS feeds,
Google search, web scraping), writes the combined results to a CSV file,
then sends the CSV content to the OpenAI model for summarization.
"""

import csv
import io
import json
import sys
import time
from datetime import datetime

from agent import ContentAgent
import jev
from config import (
    FILTER_KEYWORDS,
    GOOGLE_SEARCH_KEYWORDS,
    JEV_ANTI_PIRACY_THRESHOLD,
    JEV_DELAY_SEC,
    JEV_KEYWORD_THRESHOLD,
    JEV_MAX_ROWS,
    JEV_MAX_SUMMARY_CHARS,
    find_keyword_matches,
    validate_google_credentials,
    validate_jev_credentials,
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
    "Es_Antipirateria",
    "Infraestructura",
    "Region",
    "Tipo",
]

# ------------------------------------------------------------------
# System-level instructions sent to the model for summarization
# ------------------------------------------------------------------
SUMMARY_INSTRUCTIONS = """\
You are an anti-piracy content monitoring assistant.

You will receive the contents of a CSV file with articles collected from
RSS feeds, Google searches, and scraped web pages.  Each row was evaluated
by the Jev model, which decided relevance and stored its verdict in the
triage columns (Es_Antipirateria, Infraestructura, Region, Tipo).

Rows whose triage columns are all empty failed the relevance filters
and are kept in the CSV ONLY for manual false-negative review.  Never
include those rows in your report.

FILTER keywords used for relevance:
  {filter_keywords}

Your job is to:
  1.  Consider only rows with non-empty triage columns.
  2.  Remove duplicate articles (same URL or same headline).
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
    """Build the summarization prompt with the configured keyword list."""
    return SUMMARY_INSTRUCTIONS.format(
        filter_keywords=", ".join(FILTER_KEYWORDS),
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
# JEV
# ------------------------------------------------------------------

JEV_ANTI_PIRACY_QUESTION = {
    "type": "noul",
    "instructions": "Is this content about anti-piracy?",
}

JEV_KEYWORD_QUESTION = {
    "type": "noul",
    "instructions": (
        "Is this content relevant to at least one keyword in `keywords`? "
        "Match by meaning, synonyms and context, not only literal text."
    ),
}

JEV_TRIAGE_QUESTIONS = {
    "region": {
        "type": "choice",
        "instructions": "How much is it related to Latin America?",
        "criteria": {"Mexico": None, "Latin America": None, "Other": None},
    },
    "infrastructure": {
        "type": "choice",
        "instructions": "Which is the affected infrastructure of the piracy news?",
        "criteria": {
            "IPTV": None,
            "Conditional Access": None,
            "SaaS": None,
            "TV Box": None,
            "Cable": None,
            "Other": None,
        },
    },
    "stream_content_type": {
        "type": "choice",
        "instructions": "What is the type of content?",
        "criteria": {
            "Movies": None,
            "TV Shows": None,
            "Sports": None,
            "Sky": None,
        },
    },
}

# All questions asked in a single Jev call per row.  Jev evaluates them in
# parallel over the same state, so one request produces both the relevance
# filters and the triage verdict (no duplicated calls, lower token use).
JEV_QUESTIONS = {
    "isAntiPiracy": JEV_ANTI_PIRACY_QUESTION,
    "keywordRelevance": JEV_KEYWORD_QUESTION,
    "infrastructure": JEV_TRIAGE_QUESTIONS["infrastructure"],
    "region": JEV_TRIAGE_QUESTIONS["region"],
    "stream_content_type": JEV_TRIAGE_QUESTIONS["stream_content_type"],
}


def _compacted_state(row: dict) -> dict:
    """Return a small state for one row: keep the useful fields, truncate
    summary, and attach the configured keywords once per request."""
    return {
        "keywords": FILTER_KEYWORDS,
        "date": row.get("date", ""),
        "url": row.get("url", ""),
        "title": row.get("title", ""),
        "source": row.get("source", ""),
        "summary": row.get("summary", "")[:JEV_MAX_SUMMARY_CHARS],
    }


def _empty_verdict() -> dict:
    """Return a verdict with empty columns (used for rows that fail the Jev
    filters, so they stay in the CSV for false-negative review)."""
    return {
        "Es_Antipirateria": "",
        "Infraestructura": "",
        "Region": "",
        "Tipo": "",
    }


def _jev_delay() -> None:
    """Pause between calls when a delay is configured."""
    if JEV_DELAY_SEC:
        time.sleep(JEV_DELAY_SEC)


def _evaluate_row(state: dict) -> dict:
    """Ask Jev every question for one row in a single call.

    Returns ``noul`` (anti-piracy signal), ``keyword_noul`` (relevance
    signal) and the three triage choices, or raises on a bad answer.
    """
    response = jev.evaluate(state=state, questions=JEV_QUESTIONS)
    answers = response["answers"]

    noul = answers["isAntiPiracy"]["noul"]
    if not isinstance(noul, (int, float)):
        raise jev.JevError(f"unexpected isAntiPiracy answer: {noul!r}")

    keyword_noul = answers["keywordRelevance"]["noul"]
    if not isinstance(keyword_noul, (int, float)):
        raise jev.JevError(f"unexpected keywordRelevance answer: {keyword_noul!r}")

    return {
        "noul": float(noul),
        "keyword_noul": float(keyword_noul),
        "Infraestructura": answers["infrastructure"]["choice"],
        "Region": answers["region"]["choice"],
        "Tipo": answers["stream_content_type"]["choice"],
    }


def _jev_triage(unique_rows: list[dict]) -> list[dict]:
    """Evaluate each row with Jev (System One), row by row, in one call.

    For every row a single request asks the anti-piracy question, the
    keyword-relevance question and the triage questions together.

    A row is triaged only when ALL of these hold:

    - ``isAntiPiracy >= JEV_ANTI_PIRACY_THRESHOLD``
    - ``keywordRelevance >= JEV_KEYWORD_THRESHOLD``
    - ``Region`` is not ``"Other"``

    Rows that fail any of them are written to the CSV with the four triage
    columns empty so they can be reviewed later as potential false
    negatives.  ``matched_keywords`` is filled from literal keyword hits in
    the local text (traceability only; Jev is the one deciding relevance).
    A failed Jev call also keeps the row with empty columns.
    """
    kept: list[dict] = []
    untriaged = 0
    errors = 0

    for idx, row in enumerate(unique_rows, 1):
        state = _compacted_state(row)
        print(
            f"\r\U0001f50d JEV row {idx}/{len(unique_rows)}...",
            end="",
            file=sys.stderr,
            flush=True,
        )

        row["matched_keywords"] = ", ".join(
            find_keyword_matches(
                f"{row.get('title', '')} {row.get('summary', '')}"
            )
        )

        try:
            result = _evaluate_row(state)
        except (jev.JevError, KeyError, TypeError) as exc:
            errors += 1
            print(
                f"\n  \u26a0 row {idx} Jev evaluation failed: {exc}",
                file=sys.stderr,
                flush=True,
            )
            row.update(_empty_verdict())
            kept.append(row)
            _jev_delay()
            continue

        passes = (
            result["noul"] >= JEV_ANTI_PIRACY_THRESHOLD
            and result["keyword_noul"] >= JEV_KEYWORD_THRESHOLD
            and result["Region"] != "Other"
        )
        if not passes:
            untriaged += 1
            row.update(_empty_verdict())
            kept.append(row)
            _jev_delay()
            continue

        verdict = {
            "Es_Antipirateria": round(result["noul"], 2),
            "Infraestructura": result["Infraestructura"],
            "Region": result["Region"],
            "Tipo": result["Tipo"],
        }
        row.update(verdict)
        kept.append(row)
        _jev_delay()

    print(file=sys.stderr, flush=True)

    if untriaged:
        print(
            f"  \u26a0 {untriaged} row(s) kept without triage"
            " (failed Jev relevance filters).",
            file=sys.stderr,
            flush=True,
        )
    if errors:
        print(
            f"  \u26a0 {errors} Jev call(s) failed.",
            file=sys.stderr,
            flush=True,
        )
    return kept


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    validate_google_credentials()
    validate_openai_credentials()
    validate_jev_credentials()

    # Collect data deterministically from all three sources
    all_rows: list[dict] = []
    all_rows.extend(_collect_feeds())
    all_rows.extend(_collect_google())
    all_rows.extend(_collect_scrapes())

    # De-duplicate, run JEV triage (capped), and write the relevant rows to CSV
    unique_rows = _deduplicate(all_rows)
    triaged = unique_rows[:JEV_MAX_ROWS]
    skipped = len(unique_rows) - len(triaged)
    kept_rows = _jev_triage(triaged)

    if skipped:
        print(
            f"  \u26a0 {skipped} row(s) skipped: JEV triage capped at"
            f" {JEV_MAX_ROWS} rows.",
            file=sys.stderr,
            flush=True,
        )

    _write_csv(kept_rows, CSV_PATH)
    print(
        f"\n\U0001f4be {len(kept_rows)} entries written to {CSV_PATH}"
        f" ({len(all_rows) - len(kept_rows)} removed:"
        f" duplicates + skipped)",
        file=sys.stderr,
        flush=True,
    )

    # 3. Send CSV content to the model for summarization
    csv_text = _read_csv_as_text(CSV_PATH)
    instructions = _build_summary_instructions()

    #TODO: this is where the summarization happens, but the code adds complexity and an agent is not needed.  We can just call the model directly with the CSV text and instructions.
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
