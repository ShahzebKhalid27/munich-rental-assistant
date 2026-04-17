"""
WG-Gesucht Scraper — Playwright (Full Chromium + Stealth) Edition.

Uses Playwright with a full Chromium browser + stealth plugin
to bypass Cloudflare and JS-based bot detection.

Anti-Ban Strategy:
- Full Chromium (not headless shell — harder to detect)
- playwright-stealth plugin (patches automation tells)
- Randomized viewport, timezone, locale
- Human-like scroll + mouse movement
- Respectful delays (4–9s between pages)
- No parallel requests

NOTE: Subject to WG-Gesucht ToS. For production, consider their official API.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

from ..media import get_listing_image_path, get_listing_image_url

logger = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

WG_BASE_URL = "https://www.wg-gesucht.de"
DEFAULT_DELAY = (4.0, 9.0)
MAX_SCROLLS = 3


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


# ── Main scraper ─────────────────────────────────────────────────────────────

async def fetch_listings(params: WGSearchParams) -> list[WGListing]:
    """
    Fetch listings from WG-Gesucht using Playwright + stealth plugin.

    Returns normalized WGListing objects.
    Gracefully returns [] if blocked.
    """
    listings: list[WGListing] = []

    async with async_playwright() as p:
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
            ],
        )

        context: BrowserContext = await browser.new_context(
            viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
            locale="de-DE",
            timezone_id="Europe/Berlin",
            extra_http_headers={
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            },
        )

        page: Page = await context.new_page()
        # Apply stealth patches to hide automation signals
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            url = params.build_url()
            logger.info(f"Navigating to: {url}")

            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response is None or response.status in (403, 404, 503):
                logger.warning(
                    f"WG-Gesucht blocked (status {response.status if response else 'None'}). "
                    "URL structure may have changed or IP is blocked."
                )
                return []

            # Wait for JS to render
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # Try multiple selectors (WG-Gesucht changes layouts frequently)
            selector_patterns = [
                "div[id^='offer_list_item']",
                "div.offer_list_item",
                "div[class*='offer_list_item']",
                "article[class*='offer']",
                ".offer_list_item",
                "[data-id]",
            ]

            cards: list = []
            for pattern in selector_patterns:
                found = await page.query_selector_all(pattern)
                if found:
                    cards = found
                    logger.info(f"Found {len(cards)} cards with selector: {pattern}")
                    break

            if not cards:
                title = await page.title()
                logger.warning(f"No listing cards found. Page title: {title}")
                return []

            # Human-like scroll to trigger lazy content
            for _ in range(random.randint(1, MAX_SCROLLS)):
                await page.mouse.wheel(0, random.randint(200, 600))
                await asyncio.sleep(random.uniform(0.5, 1.5))

            await asyncio.sleep(random.uniform(1.0, 2.0))

            # Parse each card
            for card_elem in cards:
                try:
                    card_html = await card_elem.inner_html()
                    from bs4 import BeautifulSoup
                    card_soup = BeautifulSoup(card_html, "lxml")
                    listing = _parse_card_soup(card_soup)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Failed to parse card: {e}")
                    continue

            logger.info(f"Parsed {len(listings)} listings from page {params.page}")

        except Exception as e:
            logger.error(f"Scraping error: {e}")

        finally:
            await browser.close()

    return listings


def _parse_card_soup(card_soup) -> WGListing | None:
    """Parse a BeautifulSoup card element into a WGListing."""
    try:
        title_elem = (
            card_soup.select_one("h3 a, h4 a, .headline a, a[href*='zimmer'], a[href*='wohnungen']")
        )
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        href = title_elem.get("href", "")
        listing_url = href if href.startswith("http") else f"{WG_BASE_URL}{href}"
        external_id = _extract_external_id(listing_url)

        # Price
        price_elem = (
            card_soup.select_one(".col-sm-3, [class*='price'], .offer_list_price")
            or card_soup.find(string=re.compile(r"\d+\s*€"))
        )
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price_total = _parse_price(price_text)

        # Size
        size_elem = (
            card_soup.select_one(".col-sm-2, [class*='size'], .offer_list_size")
            or card_soup.find(string=re.compile(r"\d+\s*m"))
        )
        size_text = size_elem.get_text(strip=True) if size_elem else ""
        size_sqm = _parse_size(size_text)

        # Address
        address_elem = (
            card_soup.select_one(".location, [class*='district'], [class*='ort'], span[class*='ort']")
        )
        address = address_elem.get_text(strip=True) if address_elem else None

        # Description
        desc_elem = card_soup.select_one(".description, .offer_list_text, [class*='beschreibung']")
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

        # Available from
        avail_elem = (
            card_soup.select_one(".movein-date, [class*='date'], .freitext")
            or card_soup.find(string=re.compile(r"sofort|\d{1,2}\.\d{1,2}\.\d{4}"))
        )
        avail_text = avail_elem.get_text(strip=True) if avail_elem else ""
        available_from = _parse_date(avail_text)

        # Images — dedupe, limit 10
        img_elems = card_soup.select("img[src*='photos'], img[src*='wg-'], img.list-image, img")
        image_urls = []
        for img in img_elems:
            src = img.get("src") or img.get("data-src") or ""
            if src and src.startswith("http") and "pixel" not in src:
                image_urls.append(src)
        image_urls = list(dict.fromkeys(image_urls))[:10]

        return WGListing(
            external_id=external_id or str(abs(hash(title)))[:10],
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
        logger.debug(f"Card parse error: {e}")
        return None


async def fetch_multiple_pages(params: WGSearchParams, pages: int = 3) -> list[WGListing]:
    """Fetch multiple pages with human-like delays."""
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
