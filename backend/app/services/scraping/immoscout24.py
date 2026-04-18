"""
ImmoScout24 Scraper — Playwright Edition.

Source: https://www.immobilienscout24.de

Uses Playwright headless Chromium to scrape listings.
Anti-ban: stealth mode, randomized viewport/timezone, human-like delays.
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

logger = logging.getLogger(__name__)

IS24_BASE_URL = "https://www.immobilienscout24.de"
DEFAULT_DELAY = (4.0, 9.0)
MAX_SCROLLS = 3


@dataclass
class IS24SearchParams:
    city: str = "München"
    district: str | None = None
    property_type: str = "apartment"
    price_max: int | None = None
    size_min: float | None = None
    rooms_min: float | None = None
    page: int = 1

    def build_url(self) -> str:
        region = self.city.lower().replace("ü", "ue").replace(" ", "-")
        if self.property_type == "room":
            path = f"/Suche/de/{region}/zimmer"
        elif self.property_type == "house":
            path = f"/Suche/de/{region}/haus-mieten"
        else:
            path = f"/Suche/de/{region}/wohnung-mieten"

        parts = []
        if self.price_max:
            parts.append(f"price=0-{self.price_max}")
        if self.size_min:
            parts.append(f"livingspace={self.size_min}-")
        if self.rooms_min:
            parts.append(f"rooms={self.rooms_min}-")
        if self.page > 1:
            parts.append(f"pagenumber={self.page}")

        if parts:
            path += "?" + "&".join(parts)
        return f"{IS24_BASE_URL}{path}"


@dataclass
class IS24Listing:
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


def _extract_id(url: str) -> str:
    match = re.search(r"/expose/(\d+)", url)
    return match.group(1) if match else ""


async def fetch_listings(params: IS24SearchParams) -> list[IS24Listing]:
    listings: list[IS24Listing] = []

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
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            url = params.build_url()
            logger.info(f"ImmoScout24 navigating to: {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response is None or response.status in (403, 404, 503):
                logger.warning(f"ImmoScout24 blocked (status {response.status})")
                return []

            await asyncio.sleep(random.uniform(2.0, 4.0))

            selectors = [
                "article[data-is24-qa='listing']",
                ".result-list__listing",
                "[data-id^='expose']",
                ".expose-list__item",
                "div[class*='listingItem']",
                "div[id^='listing-']",
                "article",
            ]

            cards: list = []
            for pattern in selectors:
                found = await page.query_selector_all(pattern)
                if found:
                    cards = found
                    logger.info(f"Found {len(found)} cards with selector: {pattern}")
                    break

            if not cards:
                title = await page.title()
                logger.warning(f"No cards found. Page title: {title}")
                return []

            for _ in range(random.randint(1, MAX_SCROLLS)):
                await page.mouse.wheel(0, random.randint(200, 600))
                await asyncio.sleep(random.uniform(0.5, 1.5))

            await asyncio.sleep(random.uniform(1.0, 2.0))

            for card_elem in cards:
                try:
                    card_html = await card_elem.inner_html()
                    from bs4 import BeautifulSoup
                    card_soup = BeautifulSoup(card_html, "lxml")
                    listing = _parse_card(card_soup)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Parse error: {e}")
                    continue

            logger.info(f"Parsed {len(listings)} listings from page {params.page}")

        except Exception as e:
            logger.error(f"ImmoScout24 error: {e}")

        finally:
            await browser.close()

    return listings


def _parse_card(soup) -> IS24Listing | None:
    try:
        title_elem = (
            soup.select_one("h5 a, h6 a, .result-list__item-title a, a[href*='/expose/']")
        )
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        href = title_elem.get("href", "")
        if href and not href.startswith("http"):
            href = f"{IS24_BASE_URL}{href}" if href.startswith("/") else f"{IS24_BASE_URL}/{href}"
        listing_url = href

        price_elem = (
            soup.select_one("[data-is24-qa='price'], .result-list__item-price, .price")
            or soup.find(string=re.compile(r"\d+\s*€"))
        )
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price_total = _parse_price(price_text)

        cold_elem = (
            soup.select_one("[data-is24-qa='coldRent'], .cold-rent")
        )
        cold_text = cold_elem.get_text(strip=True) if cold_elem else ""
        price_cold = _parse_price(cold_text)

        size_elem = (
            soup.select_one("[data-is24-qa='livingspace'], .result-list__item-area, .area")
            or soup.find(string=re.compile(r"\d+\s*m"))
        )
        size_text = size_elem.get_text(strip=True) if size_elem else ""
        size_sqm = _parse_size(size_text)

        address_elem = soup.select_one("[data-is24-qa='address'], .result-list__item-address, .address")
        address = address_elem.get_text(strip=True) if address_elem else None

        avail_elem = (
            soup.select_one("[data-is24-qa='availableFrom'], .available-from")
            or soup.find(string=re.compile(r"sofort|\d{1,2}\.\d{1,2}\.\d{4}"))
        )
        avail_text = avail_elem.get_text(strip=True) if avail_elem else ""
        available_from = _parse_date(avail_text)

        desc_elem = soup.select_one(".result-list__item-description, .description")
        description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ""

        img_elems = soup.select("img[src*='is24static'], img[src*='cdn'], img")
        image_urls = []
        for img in img_elems:
            src = img.get("src") or img.get("data-src") or ""
            if src and "pixel" not in src:
                if src.startswith("//"):
                    src = f"https:{src}"
                elif not src.startswith("http"):
                    src = f"https://{src}"
                image_urls.append(src)
        image_urls = list(dict.fromkeys(image_urls))[:10]

        return IS24Listing(
            external_id=_extract_id(listing_url) or str(abs(hash(title)))[:10],
            title=title or "ImmoScout24 Inserat",
            description=description,
            price_total=price_total,
            price_cold=price_cold,
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


async def fetch_multiple_pages(params: IS24SearchParams, pages: int = 3) -> list[IS24Listing]:
    all_listings: list[IS24Listing] = []

    for page_num in range(1, pages + 1):
        page_params = IS24SearchParams(
            city=params.city,
            district=params.district,
            property_type=params.property_type,
            price_max=params.price_max,
            size_min=params.size_min,
            rooms_min=params.rooms_min,
            page=page_num,
        )

        listings = await fetch_listings(page_params)
        all_listings.extend(listings)
        logger.info(f"Page {page_num}/{pages}: {len(listings)} listings")

        if page_num < pages:
            delay = random.uniform(*DEFAULT_DELAY)
            logger.info(f"Sleeping {delay:.1f}s before next page")
            await asyncio.sleep(delay)

    return all_listings
