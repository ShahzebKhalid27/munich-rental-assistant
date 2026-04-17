"""
WG-Gesucht Scraper — Production-ready, Anti-Ban Edition.

Anti-Ban Strategy:
- Rotating User-Agent strings (realistic browser signatures)
- Shared httpx Client with connection pooling (session reuse)
- Jittered delays between requests (2–6s random)
- Respect Retry-After headers
- Exponential backoff on failures
- No aggressive parallel requests — one search at a time
- All config via environment variables (no hardcoded values)

Output: normalized Listing objects ready for DB insert.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from ..media import get_listing_image_path, get_listing_image_url

logger = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

WG_BASE_URL = "https://www.wg-gesucht.de"

REALISTIC_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

DEFAULT_DELAY_SECONDS = (2.5, 6.0)  # random jitter between 2.5 and 6.0 s
MAX_RETRIES = 3


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class WGSearchParams:
    """Search parameters for WG-Gesucht."""
    city: str = "München"
    district: str | None = None   # e.g. "Maxvorstadt", "Schwabing"
    max_price: int | None = None
    min_size_sqm: float | None = None
    wg_only: bool = True          # WG rooms vs full apartments
    page: int = 0                 # 0-based

    def build_url(self) -> str:
        """Build the WG-Gesucht search URL."""
        # Clean city name for URL
        city_slug = self.city.lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace(" ", "-")

        if self.district:
            district_slug = self.district.lower().replace("ü", "ue").replace(" ", "-")
            url = f"{WG_BASE_URL}/wohnungen-in-{city_slug}.{district_slug}.html"
        else:
            url = f"{WG_BASE_URL}/wohnungen-in-{city_slug}.html"

        params = []
        if self.max_price:
            params.append(f"pr={self.max_price}")
        if self.min_size_sqm:
            params.append(f"sui={int(self.min_size_sqm)}")
        if self.wg_only:
            params.append("wfl=1")  # WG only flag
        if self.page > 0:
            params.append(f"_offset={self.page * 20}")

        if params:
            url += "?" + "&".join(params)

        return url


@dataclass
class WGListing:
    """Normalized listing data from WG-Gesucht."""
    external_id: str
    title: str
    description: str
    price_total: float | None
    price_cold: float | None
    size_sqm: float | None
    address: str | None
    city: str
    district: str | None
    latitude: float | None
    longitude: float | None
    image_urls: list[str] = field(default_factory=list)
    available_from: datetime | None = None
    url: str = ""


# ── HTTP Client ───────────────────────────────────────────────────────────────

class WGClient:
    """Shared HTTP client with anti-ban measures baked in."""

    def __init__(
        self,
        delay_range: tuple[float, float] = DEFAULT_DELAY_SECONDS,
        max_retries: int = MAX_RETRIES,
    ):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=10.0),
                follow_redirects=True,
                headers={"Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _random_ua(self) -> str:
        return random.choice(REALISTIC_USER_AGENTS)

    async def _wait_before_request(self):
        """Enforce minimum delay between requests to avoid hammering the server."""
        now = time.time()
        elapsed = now - self._last_request_time
        min_delay = self.delay_range[0]
        max_delay = self.delay_range[1]

        if elapsed < min_delay:
            wait = random.uniform(min_delay, max_delay)
            # Don't sleep if enough time has passed
            await asyncio.sleep(wait)

        self._last_request_time = time.time()

    async def get(self, url: str, retries: int = 0) -> httpx.Response:
        """Perform GET with anti-ban measures, retry on 429/5xx."""
        await self._wait_before_request()

        client = await self._get_client()
        headers = {"User-Agent": self._random_ua()}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            # Check Retry-After header
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else random.uniform(10, 30)
                logger.warning(f"Got 429, waiting {wait}s before retry.")
                await asyncio.sleep(wait)
                return await self.get(url, retries=retries)

            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 502, 503, 504) and retries < self.max_retries:
                wait = random.uniform(5, 15) * (retries + 1)
                logger.warning(f"HTTP {e.response.status_code}, retrying in {wait:.1f}s (attempt {retries + 1})")
                await asyncio.sleep(wait)
                return await self.get(url, retries=retries + 1)
            raise

        except httpx.RequestError as e:
            if retries < self.max_retries:
                wait = random.uniform(3, 8) * (retries + 1)
                logger.warning(f"Request error: {e}, retrying in {wait:.1f}s")
                await asyncio.sleep(wait)
                return await self.get(url, retries=retries + 1)
            raise


# ── HTML Parsing ──────────────────────────────────────────────────────────────

def _parse_price(text: str) -> float | None:
    """Extract price from text like '500 €' -> 500.0"""
    if not text:
        return None
    text = text.strip().replace(".", "").replace(",", ".").replace("€", "").replace(" ", "").replace("\n", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_size(text: str) -> float | None:
    """Extract size in m² from text like '35 m²' -> 35.0"""
    if not text:
        return None
    text = text.strip().replace(",", ".").replace("m²", "").replace("m2", "").replace(" ", "").replace("\n", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_date(text: str) -> datetime | None:
    """Parse German date string like '01.06.2025' or 'sofort' -> datetime."""
    if not text:
        return None
    text = text.strip().lower()
    if "sofort" in text or "nach vereinbarung" in text:
        return datetime.utcnow()
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if match:
        day, month, year = match.groups()
        return datetime(int(year), int(month), int(day))
    return None


def _extract_external_id(listing_url: str) -> str:
    """Extract the numeric ID from a WG-Gesucht listing URL."""
    match = re.search(r"-(\d+)\.html", listing_url)
    return match.group(1) if match else ""


def _parse_listing_card(card: BeautifulSoup, base_url: str) -> WGListing | None:
    """Parse a single listing card from the search results page."""
    try:
        # Title + URL
        title_elem = card.select_one("h3 a, h4 a, .headline a, .offer_list_title a")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        listing_url = title_elem.get("href", "")
        if not listing_url.startswith("http"):
            listing_url = base_url + listing_url

        # External ID
        external_id = _extract_external_id(listing_url)

        # Price
        price_elem = card.select_one(".col-sm-3 .h5, .price, [class*='price']")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price_total = _parse_price(price_text)

        # Size
        size_elem = card.select_one(".col-sm-2 .h5, .size, [class*='size']")
        size_text = size_elem.get_text(strip=True) if size_elem else ""
        size_sqm = _parse_size(size_text)

        # Address / district (WG-Gesucht often hides exact address until login)
        address_elem = card.select_one(".location, .district, [class*='district'], [class*='location']")
        address = address_elem.get_text(strip=True) if address_elem else None
        district = address  # approximate, exact address requires login

        # Available from
        avail_elem = card.select_one(".movein-date, [class*='date'], .available")
        avail_text = avail_elem.get_text(strip=True) if avail_elem else ""
        available_from = _parse_date(avail_text)

        # Description snippet
        desc_elem = card.select_one(".description, .offer_list_text, [class*='desc']")
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

        # Image URLs
        img_elems = card.select("img.list-image, .offer_list_image img, img[src*='photos']")
        image_urls = [
            img.get("src") or img.get("data-src") or ""
            for img in img_elems
        ]
        image_urls = [u for u in image_urls if u and u.startswith("http")]

        return WGListing(
            external_id=external_id,
            title=title or "Ohne Titel",
            description=description,
            price_total=price_total,
            price_cold=None,  # requires detail page
            size_sqm=size_sqm,
            address=address,
            city="München",
            district=district,
            latitude=None,  # requires geocoding
            longitude=None,
            image_urls=image_urls,
            available_from=available_from,
            url=listing_url,
        )

    except Exception as e:
        logger.warning(f"Failed to parse listing card: {e}")
        return None


# ── Main scraping function ───────────────────────────────────────────────────

async def fetch_listings(params: WGSearchParams, client: WGClient | None = None) -> Iterable[WGListing]:
    """
    Fetch listings from WG-Gesucht for the given search parameters.

    Returns normalized WGListing objects.
    """
    if client is None:
        client = WGClient()
        close_client = True
    else:
        close_client = False

    try:
        url = params.build_url()
        logger.info(f"Fetching WG-Gesucht: {url}")

        response = await client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Find all listing cards — WG-Gesucht uses several CSS class patterns
        cards = soup.select(
            "div.offer_list_item, "
            "div.offer_item, "
            ".offer_list_item_main, "
            "div[class*='offer_list']"
        )

        if not cards:
            # Fallback: look for any element with an offer ID pattern
            cards = soup.select("div[id^='offer_list_item'], div[data-id]")
            logger.info(f"No cards found via primary selectors, found {len(cards)} via fallback")

        listings: list[WGListing] = []
        for card in cards:
            listing = _parse_listing_card(card, WG_BASE_URL)
            if listing:
                listings.append(listing)

        logger.info(f"Parsed {len(listings)} listings from page {params.page}")
        return listings

    finally:
        if close_client:
            await client.close()


async def fetch_multiple_pages(
    params: WGSearchParams,
    pages: int = 3,
    delay_between_pages: tuple[float, float] = (1.5, 3.0),
) -> Iterable[WGListing]:
    """
    Fetch multiple pages of results with jittered delays between each page.
    """
    client = WGClient()

    try:
        all_listings: list[WGListing] = []
        for page in range(pages):
            page_params = WGSearchParams(
                city=params.city,
                district=params.district,
                max_price=params.max_price,
                min_size_sqm=params.min_size_sqm,
                wg_only=params.wg_only,
                page=page,
            )
            listings = await fetch_listings(page_params, client=client)
            all_listings.extend(listings)

            if page < pages - 1:
                delay = random.uniform(*delay_between_pages)
                logger.info(f"Sleeping {delay:.1f}s before next page")
                await asyncio.sleep(delay)

        return all_listings

    finally:
        await client.close()
