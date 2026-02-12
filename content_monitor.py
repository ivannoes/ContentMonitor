"""Content Monitor – entry point.

Sends a natural-language prompt to the OpenAI agent, which decides
which tools to invoke (Google search, RSS feeds, etc.) and returns a
consolidated summary.
"""

import sys

from agent import ContentAgent
from config import (
    GOOGLE_SEARCH_KEYWORDS,
    PRIMARY_KEYWORDS,
    REGION_KEYWORDS,
    SECONDARY_KEYWORDS,
    validate_google_credentials,
    validate_openai_credentials,
)

# ------------------------------------------------------------------
# System-level instructions sent to the model
# ------------------------------------------------------------------
SYSTEM_INSTRUCTIONS = """\
You are an anti-piracy content monitoring assistant.

Your job is to find recent news articles related to digital piracy,
anti-piracy enforcement, illegal streaming, IPTV piracy, and related
topics in Latin-American media.

You have access to two tools:
  • **google_search** – search Google for recent articles.
  • **read_feeds** – read RSS/Atom feeds from a curated list.

Workflow:
  1.  Use ``read_feeds`` (no arguments) to pull the latest entries from
      the built-in feed list.
  2.  Use ``google_search`` for each of these search queries:
      {google_keywords}
  3.  **REGION FILTER (mandatory, highest priority):**
      Keep an article ONLY if its title or summary mentions at least one
      REGION keyword.  This filter overrides all other keyword rules —
      even if an article matches a PRIMARY keyword, discard it when no
      REGION keyword is present.
      REGION keywords: {region_keywords}
  4.  Among the articles that passed the region filter, prefer those
      whose title or summary also contains a PRIMARY keyword.
      PRIMARY keywords: {primary_keywords}
  5.  Optionally note which SECONDARY keywords also appear.
      SECONDARY keywords: {secondary_keywords}
  6.  Remove duplicate articles (same URL).
  7.  Return a numbered list of the remaining articles with:
      - Title
      - URL
      - Publication date (if available)
      - Source (feed URL or "Google Search")
      - A one-line summary

  At the end, print a short summary line:
      "Total relevant articles found: <N>"
"""


def build_prompt() -> str:
    """Build the system instructions with the configured keyword lists."""
    return SYSTEM_INSTRUCTIONS.format(
        google_keywords=", ".join(GOOGLE_SEARCH_KEYWORDS),
        region_keywords=", ".join(REGION_KEYWORDS),
        primary_keywords=", ".join(PRIMARY_KEYWORDS),
        secondary_keywords=", ".join(SECONDARY_KEYWORDS),
    )


def main() -> None:
    validate_google_credentials()
    validate_openai_credentials()

    instructions = build_prompt()
    user_prompt = (
        "Find the latest anti-piracy and digital-piracy news from "
        "the configured feeds and Google searches.  Apply the keyword "
        "filters described in your instructions and give me the final "
        "consolidated list."
    )

    agent = ContentAgent()
    answer = agent.run(user_prompt, instructions=instructions)

    print(answer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
