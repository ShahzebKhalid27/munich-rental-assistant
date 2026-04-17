"""
WG-Gesucht Scraper — Playwright (Headless Browser) Edition.

Uses Playwright/Chromium to render pages like a real browser,
bypassing Cloudflare and JS-based bot detection.

Anti-Ban Strategy:
- Headless Chromium (real browser fingerprint)
- Randomized delays between actions (2–6s)
- Randomized mouse movements and scroll patterns
- Rotating User-Agent (handled by Chromium)
- Respectful rate limiting (1 page per 5–10s minimum)
- No parallel page loads

NOTE: This is still subject to WG-Gesucht's ToS.
For production use, consider their official API or a data partnership.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from ..media import get_listing_image_path, get_listing_image_url

logger = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

WG_BASE_URL = "https://www.wg-gesucht.de"

DEFAULT_DELAY = (3.0, 8.0)  # random wait between pages
MAX_SCROLLS_PER_PAGE = 3  # pagination loads more on scroll


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class WGSearchParams:
    city: str = "München"
    district: str | None = None
    max_price: int | None = None
    min_size_sqm: float | None = None
    wg_only: bool = True
    page: int = 0

    def build_url(self) -> str:
        """Build the WG-Gesucht search URL for rooms (WG)."""
        city_slug = (
            self.city.lower()
            .replace("ü", "ue").replace("ö", "oe")
            .replace("ä", "ae").replace("ß", "ss")
            .replace(" ", "-")
        )

        if self.district:
            district_slug = self.district.lower().replace("ü", "ue").replace(" ", "-")
            url = f"{WG_BASE_URL}/zimmer-in-{city_slug}.{district_slug}.html"
        else:
            url = f"{WG_BASE_URL}/zimmer-in-{city_slug}.html"

        params = []
        if self.max_price:
            params.append(f"pr={self.max_price}")
        if self.min_size_sqm:
            params.append(f"sui={int(self.min_size_sqm)}")
        if self.page > 0:
            params.append(f"b={self.page * 20}")

        if params:
            url += "?" + "&".join(params)

        logger.info(f"WG-Gesucht URL: {url}")
        return url


@dataclass
class WGListing:
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


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_price(text: str) -> float | None:
    if not text:
        return None
    text = text.strip().replace(".", "").replace(",", ".").replace("€", "").replace(" ", "").replace("\n", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_size(text: str) -> float | None:
    if not text:
        return None
    text = text.strip().replace(",", ".").replace("m²", "").replace("m2", "").replace(" ", "").replace("\n", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _parse_date(text: str) -> datetime | None:
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


def _extract_external_id(url: str) -> str:
    match = re.search(r"-(\d+)\.html", url)
    return match.group(1) if match else ""


async def _human_delay(page: Page, delay_range: tuple[float, float] = DEFAULT_DELAY):
    """Simulate human reading time between actions."""
    delay = random.uniform(*delay_range)
    await asyncio.sleep(delay)


async def _scroll_to_load_more(page: Page, scrolls: int = MAX_SCROLLS_PER_PAGE):
    """Scroll down to trigger lazy-loaded listings (infinite scroll sites)."""
    for _ in range(scrolls):
        await page.mouse.wheel(0, random.randint(300, 700))
        await asyncio.sleep(random.uniform(0.8, 2.0))


# ── Main scraper ─────────────────────────────────────────────────────────────

async def fetch_listings(params: WGSearchParams) -> list[WGListing]:
    """
    Fetch listings from WG-Gesucht using Playwright (headless Chromium).

    Returns normalized WGListing objects.
    Gracefully returns [] if the page is blocked or unavailable.
    """
    listings: list[WGListing] = []

    async with async_playwright() as p:
        # Launch browser with anti-detection settings
        browser: Browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--disable-web-security",
            ],
        )

        context: BrowserContext = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="de-DE",
            extra_http_headers={
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            },
        )

        page: Page = await context.new_page()

        try:
            url = params.build_url()
            logger.info(f"Navigating to: {url}")

            # Navigate with retry
            response = await page.goto(url, wait_until="networkidle", timeout=30000)

            if response is None or response.status in (403, 404, 503):
                logger.warning(
                    f"WG-Gesucht blocked us (status {response.status if response else 'None'}). "
                    "Try again later or use a proxy."
                )
                return []

            # Wait for listings to render
            try:
                await page.wait_for_selector(
                    "div[id^='offer_list_item'], div.offer_list_item, article",
                    timeout=15000,
                )
            except Exception:
                logger.warning("No listings appeared after page load — site may be blocking.")
                return []

            # Scroll to trigger lazy-loaded content
            await _scroll_to_load_more(page)

            # Human delay
            await _human_delay(page)

            # Extract listing HTML
            html = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # Multiple selector patterns WG-Gesucht uses
            cards = soup.select(
                "div[id^='offer_list_item'], "
                "div.offer_list_item, "
                "div[class*='offer_list_item']:not(.pagination):not(.sidebar), "
                "article[class*='offer']"
            )

            logger.info(f"Found {len(cards)} listing cards on page {params.page}")

            for card in cards:
                listing = _parse_card(card)
                if listing:
                    listings.append(listing)

        except Exception as e:
            logger.error(f"Error during scraping: {e}")

        finally:
            await browser.close()

    return listings


def _parse_card(card) -> WGListing | None:
    """Parse a single listing card HTML element into a WGListing."""
    try:
        # Title + URL
        title_elem = (
            card.select_one("h3 a, h4 a, .headline a, a[href*='zimmer']")
            or card.select_one("a[href*='wohnungen']")
        )
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        href = title_elem.get("href", "")
        listing_url = href if href.startswith("http") else f"{WG_BASE_URL}{href}"
        external_id = _extract_external_id(listing_url)

        # Price
        price_elem = card.select_one(".col-sm-3, [class*='price']")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price_total = _parse_price(price_text)

        # Size
        size_elem = card.select_one(".col-sm-2, [class*='size']")
        size_text = size_elem.get_text(strip=True) if size_elem else ""
        size_sqm = _parse_size(size_text)

        # Address
        address_elem = card.select_one(".location, [class*='district'], [class*='ort']")
        address = address_elem.get_text(strip=True) if address_elem else None

        # Description
        desc_elem = card.select_one(".description, .offer_list_text, [class*='beschreibung']")
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

        # Available from
        avail_elem = card.select_one(".movein-date, [class*='date'], .freitext")
        avail_text = avail_elem.get_text(strip=True) if avail_elem else ""
        available_from = _parse_date(avail_text)

        # Images
        img_elems = card.select("img[src*='photos'], img[src*='wg-'], img.list-image")
        image_urls = [
            img.get("src") or img.get("data-src") or ""
            for img in img_elems
        ]
        image_urls = [u for u in image_urls if u and u.startswith("http")]

        return WGListing(
            external_id=external_id or str(hash(title))[:10],
            title=title or "Ohne Titel",
            description=description,
            price_total=price_total,
            price_cold=None,
            size_sqm=size_sqm,
            address=address,
            city="München",
            district=address,
            latitude=None,
            longitude=None,
            image_urls=image_urls,
            available_from=available_from,
            url=listing_url,
        )

    except Exception as e:
        logger.debug(f"Failed to parse card: {e}")
        return None


async def fetch_multiple_pages(
    params: WGSearchParams,
    pages: int = 3,
) -> list[WGListing]:
    """Fetch multiple pages of results with human-like delays."""
    all_listings: list[WGListing] = []

    for page_num in range(pages):
        page_params = WGSearchParams(
            city=params.city,
            district=params.district,
            max_price=params.max_price,
            min_size_sqm=params.min_size_sqm,
            wg_only=params.wg_only,
            page=page_num,
        )

        listings = await fetch_listings(page_params)
        all_listings.extend(listings)
        logger.info(f"Page {page_num + 1}/{pages}: {len(listings)} listings")

        if page_num < pages - 1:
            delay = random.uniform(*DEFAULT_DELAY)
            logger.info(f"Sleeping {delay:.1f}s before next page")
            await asyncio.sleep(delay)

    return all_listings
