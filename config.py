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
# PRIMARY keywords (must be present)
# ---------------------------------------------------------------------------
PRIMARY_KEYWORDS = [
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

# ---------------------------------------------------------------------------
# SECONDARY keywords (must appear alongside a primary one)
# ---------------------------------------------------------------------------
SECONDARY_KEYWORDS = [
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

# ---------------------------------------------------------------------------
# REGION keywords (article must mention a Latin-American region to be kept)
# ---------------------------------------------------------------------------
REGION_KEYWORDS = [
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
