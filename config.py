"""Centralized configuration for the Content Monitor."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Google API
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Jev (System One) via OpenCode Zen
# ---------------------------------------------------------------------------
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
JEV_MODEL = os.getenv("JEV_MODEL", "jev-1.13-free")
JEV_SYSTEM_ONE_URL = os.getenv(
    "JEV_SYSTEM_ONE_URL", "https://opencode.ai/zen/v1/systemone"
)
# Truncate each row's summary before sending it as state.
JEV_MAX_SUMMARY_CHARS = int(os.getenv("JEV_MAX_SUMMARY_CHARS", "300"))
# Only triage up to this many unique rows (keeps free-model token usage bounded).
JEV_MAX_ROWS = int(os.getenv("JEV_MAX_ROWS", "100"))
# A row is considered anti-piracy content when Jev's noul probability
# is at least this value.
JEV_ANTI_PIRACY_THRESHOLD = float(os.getenv("JEV_ANTI_PIRACY_THRESHOLD", "0.65"))
# A row must score at least this high on the keyword-relevance question
# to be triaged.
JEV_KEYWORD_THRESHOLD = float(os.getenv("JEV_KEYWORD_THRESHOLD", "0.65"))
# Optional pause between calls (rate-limit safety).
JEV_DELAY_SEC = float(os.getenv("JEV_DELAY_SEC", "1.7"))

# ---------------------------------------------------------------------------
# RSS feeds from Latin American media (cleaned and validated)
# ---------------------------------------------------------------------------
RSS_FEEDS = [
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

# ---------------------------------------------------------------------------
# Web pages to scrape (homepages, forum listings, directory pages)
# ---------------------------------------------------------------------------
SCRAPE_URLS = [
    "https://torrentfreak.com/category/piracy/",
    "https://torrentfreak.com/category/research/",
    "https://torrentfreak.com/category/law-politics/",
    "https://torrentfreak.com/category/lawsuits/",
    "https://torrentfreak.com/category/anti-piracy/",
    "https://torrentfreak.com/category/technology/",
    "https://piracymonitor.org/newsfeed/",
    "https://www.alliance4creativity.com/news/",    
    "https://ipuntotv.com/",
    "https://alianzaaudiovisual.net/noticias.php",
    "https://dplnews.com/tag/pirateria/",
    "https://www.forokeys.com/foro/viark-sat/",
    "https://www.forokeys.com/foro/viark-sat-4k/",
    "https://www.forokeys.com/foro/viark-combo/",
    "https://www.forokeys.com/foro/viark-lil/",
    "https://www.forokeys.com/foro/viark-lil-2/",
    "https://www.forokeys.com/foro/viark-droi/",
    "https://www.forokeys.com/foro/viark-drs/",
    "https://www.forokeys.com/foro/viark-drs2/",
    "https://www.forokeys.com/foro/qviart-dual-receptor-satelite-y-tdt-4k-uhd-linux-enigma2-android-9-0*/",
    "https://ipuntotv.com/Notas%202/archivo_9.html",
]

# ---------------------------------------------------------------------------
# PRIMARY keywords (source list, merged into FILTER_KEYWORDS below)
# ---------------------------------------------------------------------------
_PRIMARY_KEYWORDS = [
    "anti pirateria",
    "anti piratería",
    "anti-pirateria",
    "anti-piratería",
    "antipirateria",
    "antipiratería",
    "pirateria",
    "piratería",
    "operativo",
    "bloqueo",
    "cardsharing",
    "IPTV",
    "decodificadores",
    "VIARK",
    "LaLiga Content Protection",
    "decodificador",
    "receptor",
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
    "streaming",
    "ilegal",
    "sitio pirata",
    "combate a la ciberdelincuencia",
    "combate a la pirateria",
    "medida contra la pirateria",
    "Desmantelan red",
    "derechos",
    "indecopi",
    "IMPI",
    "Gabriel Drouet",
    "Tebas",
    "javier tebas",
    "jorge bacaloni",
    "fraude audiovisual",
    "Ley",
    "copyright",
    "firmware",
]

# ---------------------------------------------------------------------------
# SECONDARY keywords (source list, merged into FILTER_KEYWORDS below)
# ---------------------------------------------------------------------------
_SECONDARY_KEYWORDS = [
    "contra la",
    "lucha contra la",
    "de streaming",
    "red de",
    "de televisión",
    "de canales",
    "de señal",
    "de operativo",
    "investigación",
    "delito",
    "ilegal",
    "pirata",
    "digital",
    "audiovisual",
    "en línea",
    "Online",
    "de TV",
    "operativo",
    "dinámico",
    "de sitios",
    "de IP",
    "de plataformas",
    "venta de",
    "Desbloqueo",
    "SKY",
    "Megacable",
    "DirecTV",
    "Cablevisión",
    "de fútbol",
    "de decodificadores",
    "ilegal",
    "sitio de",
    "páginas de",
    "de contenido",
    "difusión",
    "contenido",
    "de autor",
    "de Propiedad Intelectual",
]

# ---------------------------------------------------------------------------
# REGION keywords (source list, merged into FILTER_KEYWORDS below)
# ---------------------------------------------------------------------------
_REGION_KEYWORDS = [
    "VIARK",
    # -- Countries --
    "México",
    "Mexico",
    "Colombia",
    "Argentina",
    "Chile",
    "Perú",
    "Peru",
    "Brasil",
    "Brazil",
    "Venezuela",
    "Ecuador",
    "Bolivia",
    "Paraguay",
    "Uruguay",
    "Cuba",
    "Costa Rica",
    "Panamá",
    "Guatemala",
    "Honduras",
    "El Salvador",
    "Nicaragua",
    "República Dominicana",
    "Puerto Rico",
    # -- Regions / Demonyms --
    "América Latina",
    "Latinoamérica",
    "LATAM",
    "Centroamérica",
    "Sudamérica",
    "Caribe",
    "latinoamericano",
    "latinoamericana",
    # -- Major cities --
    "Ciudad de México",
    "CDMX",
    "Bogotá",
    "Buenos Aires",
    "Santiago",
    "Lima",
    "São Paulo",
    "Sao Paulo",
    "Río de Janeiro",
    "Caracas",
    "Quito",
    "Montevideo",
    "Guadalajara",
    "Monterrey",
    "Medellín",
    # -- Regional organizations & regulators --
    "INDECOPI",
    "IMPI",
    "IFT",
    "Megacable",
    "Televisa",
    "TV Azteca",
    "Claro",
    "Telmex",
    "Mercosur",
    "Liga MX",
]

# ---------------------------------------------------------------------------
# FILTER_KEYWORDS -- single merged, deduplicated list used by the JEV
# relevance questions.  Region, primary and secondary terms are no longer
# treated as separate gates; they are one flat list that Jev evaluates
# semantically.
# ---------------------------------------------------------------------------

def _merge_keywords(*lists: list[str]) -> list[str]:
    """Merge keyword lists into one, keeping order and removing duplicates
    case-insensitively."""
    seen: set[str] = set()
    merged: list[str] = []
    for words in lists:
        for word in words:
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(word)
    return merged


FILTER_KEYWORDS = _merge_keywords(
    _PRIMARY_KEYWORDS, _SECONDARY_KEYWORDS, _REGION_KEYWORDS
)

# ---------------------------------------------------------------------------
# Google search keywords (subset of FILTER_KEYWORDS used for Google queries)
# ---------------------------------------------------------------------------
GOOGLE_SEARCH_KEYWORDS = [
    "antipirateria",
    "pirateria",
    "piratería audiovisual",
    "iptv",
    "streaming ilegal",
    "golpe a la pirateria",
    "cardsharing",
    "VIARK",
]


def find_keyword_matches(text: str) -> list[str]:
    """Return the keywords from ``FILTER_KEYWORDS`` that appear literally in
    *text* (case-insensitive).

    This is only used to fill the ``matched_keywords`` CSV column for
    traceability.  Relevance filtering itself is decided by Jev, not here.
    """
    text_lower = text.lower()
    return [kw for kw in FILTER_KEYWORDS if kw.lower() in text_lower]


def validate_google_credentials() -> None:
    """Exit early if Google API credentials are missing."""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("Error: Google API credentials are not configured in the .env file")
        sys.exit(1)


def validate_openai_credentials() -> None:
    """Exit early if OpenAI API key is missing."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not configured in the .env file")
        sys.exit(1)


def validate_jev_credentials() -> None:
    """Exit early if the OpenCode Zen API key is missing."""
    if not OPENCODE_API_KEY:
        print("Error: OPENCODE_API_KEY is not configured in the .env file")
        sys.exit(1)
