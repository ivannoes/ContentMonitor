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
# PRIMARY keywords (must be present)
# ---------------------------------------------------------------------------
PRIMARY_KEYWORDS = [
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
# SECONDARY keywords (must appear alongside a primary one)
# ---------------------------------------------------------------------------
SECONDARY_KEYWORDS = [
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
# REGION keywords (article must mention a Latin-American region to be kept)
# ---------------------------------------------------------------------------
REGION_KEYWORDS = [
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
# Google search keywords (subset of primary keywords used for Google queries)
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


def matches_keywords(text: str) -> tuple[bool, list[str]]:
    """Check whether *text* passes the mandatory keyword filters.

    Returns ``(passes, matched_keywords)`` where *passes* is ``True``
    only when **both** conditions are met:

    1.  At least one **REGION** keyword is found (mandatory gate).
    2.  At least one **PRIMARY** or **SECONDARY** keyword is also found.

    This is the single source of truth for keyword filtering, used by
    every tool so the logic stays consistent.
    """
    text_lower = text.lower()

    region_hits = [kw for kw in REGION_KEYWORDS if kw.lower() in text_lower]
    if not region_hits:
        return False, []

    primary_hits = [kw for kw in PRIMARY_KEYWORDS if kw.lower() in text_lower]
    secondary_hits = [kw for kw in SECONDARY_KEYWORDS if kw.lower() in text_lower]

    if not primary_hits and not secondary_hits:
        return False, []

    return True, primary_hits + secondary_hits + region_hits


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
