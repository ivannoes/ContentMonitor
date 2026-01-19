import sys
import feedparser
import pandas as pd
import requests
import time
from datetime import datetime
from googleapiclient.discovery import build
from utils import printJSON
from googleapiclient.errors import HttpError
from urllib.parse import urlparse
import logging

import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Key and Search Engine ID from environment variables
my_api_key = os.getenv("GOOGLE_API_KEY")
my_cse_id = os.getenv("GOOGLE_CSE_ID")

if not my_api_key or not my_cse_id:
    logger.error("Error: Google API credentials are not configured in the .env file")
    sys.exit(1)

# List of RSS feeds from Latin American media (cleaned and validated version)
rss_feeds = [
    "https://www.excelsior.com.mx/rss.xml",
    "https://www.elfinanciero.com.mx/rss",
    "https://www.sinembargo.mx/feed",
    "https://www.informador.mx/rss/mexico.xml",
    "https://www.clarin.com/rss/lo-ultimo/",
    "https://torrentfreak.com/feed/",
    "https://piracymonitor.org/feed/",
    "https://computerhoy.20minutos.es/rss/ultimo",
    "https://www.alliance4creativity.com/feed/",
    "https://www.panoramaaudiovisual.com/feed/",
    "https://hnrss.org/newest",
    "https://hnrss.org/frontpage",
    "https://www.elespanol.com/rss/",
]

# PRIMARY keywords (must be present)
primary_keywords = [
    "antipirateria",
    "pirateria",
    "piratería digital",
    "piratería en línea",
    "alianza contra la pirateria",
    "pirateria audiovisual",
    "pirateria online",
    "contra servicios piratas",
    "señales piratas",
    "operativo antipirateria",
    "bloqueo dinámico",
    "bloqueo de sitios",
    "bloqueos IP",
    "bloqueo de plataformas",
    "cardsharing",
    "IPTV pirata",
    "red de IPTV",
    "venta de decodificadores",
    "Desbloqueo SKY",
    "VIARK",
    "Megacable",
    "DirecTV",
    "Cablevisión",
    "LaLiga Content Protection",
    "javier tebas",
    "jorge bacaloni",
    "futbol pirata",
    "decodificador",
    "receptor de señal",
    "señal robada",
    "piracy shield",
    "Blackhole",
    "Lumière",
    "Neko",
    "Sentry",
    "Vento",
    "Sportian",
    "decomiso",
    "incautación",
    "ciberdelincuencia",
    "streaming ilegal",
    "contenido ilegal",
    "difusión ilegal",
    "sitio de streaming",
    "sitio pirata",
    "combate a la ciberdelincuencia",
    "combate a la pirateria",
    "medida contra la pirateria",
    "Desmantelan red",
    "lucha contra la piratería",
    "derechos de contenido",
    "páginas de streaming",
    "indecopi",
    "IMPI",
    "Gabriel Drouet",
    "Tebas",
    "fraude audiovisual",
    "Ley de Propiedad Intelectual",
    "copyright",
    "derechos de autor",
    "propiedad intelectual",
]

# SECONDARY keywords (must be present along with a primary one)
secondary_keywords = [
    "streaming",
    "IPTV",
    "televisión",
    "canales",
    "señales",
    "bloqueo",
    "cierre",
    "operativo",
    "investigación",
    "delito",
    "ilegal",
    "pirata",
]

# EXCLUSION keywords (if present, the article is discarded)
exclusion_keywords = [
    "perro",
    "perrito",
    "lomito",
    "animal",
    "cocina",
    "receta",
    "comida",
    "restaurante",
    "clima",
    "lluvia",
    "temperatura",
    "arqueología",
    "momia",
    "antigüedad",
    "civilización",
    "circo",
    "festival",
    "arte",
    "teatro",
    "trans",
    "lgbt",
    "diversidad",
    "género",
    "crematorio",
    "funeral",
    "muerte",
    "fallecimiento",
    "anime",
    "manga",
    "dibujo",
    "animación",
    "música",
    "concierto",
    "cantante",
    "artista",
    "turismo",
    "viaje",
    "hotel",
    "vacaciones",
]


def validate_url(url):
    """Validate if a URL is accessible"""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def test_feed_accessibility(feed_url, timeout=10):
    """Test if an RSS feed is accessible"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(feed_url, timeout=timeout, headers=headers)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Could not access {feed_url}: {e}")
        return False


def google_search(search_term, **kwargs):
    """Enhanced Google search function with error handling"""
    try:
        service = build(
            "customsearch", "v1", developerKey=my_api_key, cache_discovery=False
        )
        res = (
            service.cse()
            .list(q=search_term, cx=my_cse_id, dateRestrict="w1", **kwargs)
            .execute()
        )
        return res["items"] if "items" in res else []
    except Exception as e:
        logger.error(f"Error in Google search for '{search_term}': {e}")
        return []


def contains_exclusion_keywords(content):
    """Check if content contains exclusion keywords"""
    if not content:
        return False

    content_lower = content.lower()

    for exclusion_word in exclusion_keywords:
        if exclusion_word.lower() in content_lower:
            return True

    return False


def search_in_content_strict(content, primary_keywords, secondary_keywords):
    """Strict search requiring at least one primary keyword"""
    if not content:
        return False

    content_lower = content.lower()

    # Check if it contains exclusion keywords
    if contains_exclusion_keywords(content):
        return False

    # Check if it contains at least one primary keyword
    primary_found = False
    found_primary_keywords = []

    for keyword in primary_keywords:
        if keyword.lower() in content_lower:
            primary_found = True
            found_primary_keywords.append(keyword)

    if not primary_found:
        return False

    # If it's from specialized piracy feeds, accept directly
    specialized_feeds = [
        "torrentfreak.com",
        "piracymonitor.org",
        "alliance4creativity.com",
    ]

    # Check if there are secondary keywords (optional but improves relevance)
    secondary_found = False
    found_secondary_keywords = []

    for keyword in secondary_keywords:
        if keyword.lower() in content_lower:
            secondary_found = True
            found_secondary_keywords.append(keyword)

    # Log found keywords
    logger.info(f"Primary keywords found: {found_primary_keywords}")
    if found_secondary_keywords:
        logger.info(f"Secondary keywords found: {found_secondary_keywords}")

    return True


def process_rss_feed(feed_url, primary_keywords, secondary_keywords, timeout=30):
    """Process an RSS feed with strict filtering"""
    articles_found = []

    try:
        logger.info(f"Processing feed: {feed_url}")

        # Configure feedparser with timeout
        feed = feedparser.parse(feed_url)

        if hasattr(feed, "status") and feed.status != 200:
            logger.warning(f"Feed {feed_url} returned status {feed.status}")
            return articles_found

        if not hasattr(feed, "entries") or not feed.entries:
            logger.warning(f"No entries found in feed: {feed_url}")
            return articles_found

        logger.info(f"Found {len(feed.entries)} articles in {feed_url}")

        for entry in feed.entries:
            try:
                # Combine title and summary for search
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or ""
                content = f"{title} {summary}".strip()

                if search_in_content_strict(
                    content, primary_keywords, secondary_keywords
                ):
                    logger.info(f"✅ RELEVANT match found in: {title}")

                    # Get publication date
                    published_parsed = ""
                    try:
                        if (
                            hasattr(entry, "published_parsed")
                            and entry.published_parsed
                        ):
                            published_parsed = datetime(
                                *entry.published_parsed[:6]
                            ).strftime("%Y-%m-%d")
                        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                            published_parsed = datetime(
                                *entry.updated_parsed[:6]
                            ).strftime("%Y-%m-%d")
                    except Exception as e:
                        logger.debug(f"Error processing date: {e}")

                    article_data = {
                        "Fecha de la fuente": published_parsed,
                        "URL": getattr(entry, "link", ""),
                        "Título": title,
                        "Resumen": summary,
                        "Fuente": feed_url,
                    }
                    articles_found.append(article_data)
                else:
                    logger.debug(f"❌ Article discarded: {title}")

            except Exception as e:
                logger.error(f"Error processing feed entry {feed_url}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error processing feed {feed_url}: {e}")

    return articles_found


def main():
    """Main function with strict filtering"""
    all_articles = []

    # Filter valid feeds
    valid_feeds = [feed for feed in rss_feeds if validate_url(feed)]
    logger.info(
        f"Processing {len(valid_feeds)} valid feeds out of {len(rss_feeds)} total"
    )

    # Process RSS feeds
    for feed_url in valid_feeds:
        try:
            articles = process_rss_feed(feed_url, primary_keywords, secondary_keywords)
            all_articles.extend(articles)
            time.sleep(1)  # Pause between requests to avoid overloading servers
        except Exception as e:
            logger.error(f"Error processing feed {feed_url}: {e}")
            continue

    # Process Google searches (only primary keywords)
    logger.info("Starting Google searches...")
    google_keywords = [
        "antipirateria",
        "pirateria",
        "piratería digital",
        "IPTV pirata",
        "streaming ilegal",
        "bloqueo sitios",
        "cardsharing",
        "VIARK",
    ]

    for keyword in google_keywords:
        try:
            logger.info(f"Searching Google: {keyword}")
            search_results = google_search(
                keyword, num=5
            )  # Reduce to 5 results per keyword

            for result in search_results:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                content = f"{title} {snippet}"

                # Apply same strict filtering to Google results
                if search_in_content_strict(
                    content, primary_keywords, secondary_keywords
                ):
                    article_data = {
                        "Fecha de la fuente": "",
                        "URL": result.get("link", ""),
                        "Título": title,
                        "Resumen": snippet,
                        "Fuente": "Google Search",
                    }
                    all_articles.append(article_data)
                    logger.info(f"✅ Relevant Google result: {title}")
                else:
                    logger.debug(f"❌ Google result discarded: {title}")

            time.sleep(2)  # Pause between Google searches

        except Exception as e:
            logger.error(f"Error in Google search for '{keyword}': {e}")
            continue

    # Create DataFrame and drop duplicates
    if all_articles:
        df = pd.DataFrame(all_articles)
        df.drop_duplicates(subset="URL", inplace=True)

        # Save to CSV
        csv_filename = "antipirateria_articulos_filtrados.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        logger.info(
            f"Saved {len(df)} unique and relevant articles to '{csv_filename}'"
        )

        # Show summary
        print(f"\n=== SUMMARY ===")
        print(f"Total relevant articles found: {len(df)}")
        print(f"Feeds processed: {len(valid_feeds)}")
        print(f"File saved: {csv_filename}")

        # Show some found titles
        if len(df) > 0:
            print(f"\nTop 5 relevant articles found:")
            for i, row in df.head().iterrows():
                print(f"{i+1}. {row['Título']}")
        else:
            print(
                "No relevant articles found after strict filtering"
            )
    else:
        logger.warning(
            "No articles found matching strict criteria"
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"General script error: {e}")
        sys.exit(1)
