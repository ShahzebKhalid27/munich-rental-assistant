"""
Listings API v1 — CRUD + scraping trigger + filtering + matching.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from ...db import get_db
from ...models import Listing, ListingImage, SearchProfile
from ..schemas import ListingResponse, ListingListResponse
from ...services.matching import get_top_matches, is_match_hard

logger = logging.getLogger(__name__)
router = APIRouter()


# ── GET /api/v1/listings ────────────────────────────────────────────────────

@router.get("/", response_model=ListingListResponse)
async def list_listings(
    db: Annotated[Session, Depends(get_db)],
    city: str | None = Query(None),
    district: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_size: float | None = Query(None, ge=0),
    max_size: float | None = Query(None),
    wg_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ListingListResponse:
    """List listings with optional filters. Default: last 10 days only."""

    query = select(Listing).options(joinedload(Listing.images))

    if city:
        query = query.where(Listing.city == city)
    else:
        query = query.where(Listing.city == "München")

    if district:
        query = query.where(Listing.district == district)
    if min_price is not None:
        query = query.where(Listing.price_total >= min_price)
    if max_price is not None:
        query = query.where(Listing.price_total <= max_price)
    if min_size is not None:
        query = query.where(Listing.size_sqm >= min_size)
    if max_size is not None:
        query = query.where(Listing.size_sqm <= max_size)
    if wg_only:
        query = query.where(
            Listing.title.ilike("%zimmer%")
            | Listing.title.ilike("%wg%")
            | Listing.title.ilike("%room%")
        )

    # Default: only listings newer than 10 days
    cutoff = datetime.utcnow() - timedelta(days=10)
    query = query.where(Listing.created_at >= cutoff)

    # Count
    count_q = select(func.count()).select_from(Listing)
    if city:
        count_q = count_q.where(Listing.city == city)
    else:
        count_q = count_q.where(Listing.city == "München")
    if district:
        count_q = count_q.where(Listing.district == district)
    if min_price is not None:
        count_q = count_q.where(Listing.price_total >= min_price)
    if max_price is not None:
        count_q = count_q.where(Listing.price_total <= max_price)
    if min_size is not None:
        count_q = count_q.where(Listing.size_sqm >= min_size)
    if max_size is not None:
        count_q = count_q.where(Listing.size_sqm <= max_size)
    count_q = count_q.where(Listing.created_at >= cutoff)

    total = db.scalar(count_q) or 0
    query = query.order_by(Listing.created_at.desc()).offset(offset).limit(limit)
    results = db.scalars(query).unique().all()

    listings = [
        ListingResponse(
            id=lst.id,
            external_id=lst.external_id,
            source=lst.source,
            title=lst.title,
            description=lst.description,
            price_total=lst.price_total,
            price_cold=lst.price_cold,
            size_sqm=lst.size_sqm,
            address=lst.address,
            city=lst.city,
            district=lst.district,
            latitude=lst.latitude,
            longitude=lst.longitude,
            available_from=lst.available_from,
            image_urls=[img.source_url for img in lst.images if img.source_url],
            created_at=lst.created_at,
        )
        for lst in results
    ]

    return ListingListResponse(results=listings, total=total, offset=offset, limit=limit)


# ── GET /api/v1/listings/{id} ────────────────────────────────────────────────

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int, db: Annotated[Session, Depends(get_db)]) -> ListingResponse:
    listing = db.scalars(
        select(Listing)
        .options(joinedload(Listing.images))
        .where(Listing.id == listing_id)
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingResponse(
        id=listing.id,
        external_id=listing.external_id,
        source=listing.source,
        title=listing.title,
        description=listing.description,
        price_total=listing.price_total,
        price_cold=listing.price_cold,
        size_sqm=listing.size_sqm,
        address=listing.address,
        city=listing.city,
        district=listing.district,
        latitude=listing.latitude,
        longitude=listing.longitude,
        available_from=listing.available_from,
        image_urls=[img.source_url for img in listing.images if img.source_url],
        created_at=listing.created_at,
    )


# ── GET /api/v1/listings/match/{profile_id} ────────────────────────────────

@router.get("/match/{profile_id}")
async def match_listings(
    profile_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
    use_llm: bool = Query(False),
) -> dict:
    """Top-matching listings for a user's search profile."""
    profile = db.scalars(
        select(SearchProfile).where(
            SearchProfile.id == profile_id,
            SearchProfile.is_active == True,
        )
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")

    listings = db.scalars(
        select(Listing)
        .options(joinedload(Listing.images))
        .order_by(Listing.created_at.desc())
        .limit(200)
    ).unique().all()

    top_matches = await get_top_matches(listings, profile, limit=limit, use_llm=use_llm)

    return {
        "profile_id": profile_id,
        "profile_name": profile.name,
        "total_scanned": len(listings),
        "matches_found": len(top_matches),
        "use_llm": use_llm,
        "results": [
            {
                "listing_id": listing.id,
                "title": listing.title,
                "price_total": listing.price_total,
                "size_sqm": listing.size_sqm,
                "district": listing.district,
                "image_urls": [img.source_url for img in listing.images if img.source_url],
                "score": round(score, 3),
                "explanation": explanation,
            }
            for listing, score, explanation in top_matches
        ],
    }


# ── POST /api/v1/listings/scrape ─────────────────────────────────────────────

@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    source: str = Query("wg_gesucht", description="wg_gesucht or immoscout24"),
    city: str = Query("München"),
    district: str | None = Query(None),
    max_price: int | None = Query(None),
    min_size_sqm: float | None = Query(None),
    pages: int = Query(2, ge=1, le=10),
) -> dict:
    """
    Trigger a scrape job in the background.

    Supported sources:
    - wg_gesucht: WG rooms (default)
    - immoscout24: apartments and rooms from ImmoScout24
    """
    background_tasks.add_task(
        _scrape_and_save_task,
        source=source,
        city=city,
        district=district,
        max_price=max_price,
        min_size_sqm=min_size_sqm,
        pages=pages,
    )

    return {
        "status": "started",
        "source": source,
        "message": f"Scraping {source} for {city}" + (f" ({district})" if district else ""),
        "pages": pages,
        "check_results_at": "/api/v1/listings",
    }


async def _scrape_and_save_task(
    source: str,
    city: str,
    district: str | None,
    max_price: int | None,
    min_size_sqm: float | None,
    pages: int,
):
    """Background task: scrape source and persist results to DB."""
    from ...db import SessionLocal
    from ...models import Listing, ListingImage

    logger_ = logging.getLogger(__name__)

    try:
        if source == "immoscout24":
            from ...services.scraping.immoscout24 import fetch_multiple_pages, IS24SearchParams
            params = IS24SearchParams(
                city=city,
                district=district,
                price_max=max_price,
                size_min=min_size_sqm,
            )
            raw_listings = await fetch_multiple_pages(params, pages=pages)

            db = SessionLocal()
            try:
                new_count = 0
                for raw in raw_listings:
                    existing = db.scalars(
                        select(Listing).where(
                            Listing.external_id == raw.external_id,
                            Listing.source == "immoscout24",
                        )
                    ).first()
                    if existing:
                        existing.title = raw.title
                        existing.description = raw.description
                        existing.price_total = raw.price_total
                        existing.size_sqm = raw.size_sqm
                        existing.available_from = raw.available_from
                        existing.updated_at = datetime.utcnow()
                    else:
                        listing = Listing(
                            external_id=raw.external_id,
                            source="immoscout24",
                            title=raw.title,
                            description=raw.description,
                            price_total=raw.price_total,
                            price_cold=raw.price_cold,
                            size_sqm=raw.size_sqm,
                            address=raw.address,
                            city=raw.city or city,
                            district=raw.district,
                            latitude=raw.latitude,
                            longitude=raw.longitude,
                            available_from=raw.available_from,
                        )
                        db.add(listing)
                        db.flush()
                        for img_url in raw.image_urls:
                            db.add(ListingImage(listing_id=listing.id, source_url=img_url))
                        new_count += 1
                db.commit()
                logger_.info(f"ImmoScout24 scraping complete: {new_count} new listings saved.")
            finally:
                db.close()

        else:
            # Default: WG-Gesucht
            from ...services.scraping.wg_gesucht import fetch_multiple_pages, WGSearchParams
            params = WGSearchParams(
                city=city,
                district=district,
                max_price=max_price,
                min_size_sqm=min_size_sqm,
                wg_only=True,
            )
            raw_listings = await fetch_multiple_pages(params, pages=pages)

            db = SessionLocal()
            try:
                new_count = 0
                for raw in raw_listings:
                    existing = db.scalars(
                        select(Listing).where(
                            Listing.external_id == raw.external_id,
                            Listing.source == "wg_gesucht",
                        )
                    ).first()
                    if existing:
                        existing.title = raw.title
                        existing.description = raw.description
                        existing.price_total = raw.price_total
                        existing.size_sqm = raw.size_sqm
                        existing.available_from = raw.available_from
                        existing.updated_at = datetime.utcnow()
                    else:
                        listing = Listing(
                            external_id=raw.external_id,
                            source="wg_gesucht",
                            title=raw.title,
                            description=raw.description,
                            price_total=raw.price_total,
                            price_cold=raw.price_cold,
                            size_sqm=raw.size_sqm,
                            address=raw.address,
                            city=raw.city or city,
                            district=raw.district,
                            latitude=raw.latitude,
                            longitude=raw.longitude,
                            available_from=raw.available_from,
                        )
                        db.add(listing)
                        db.flush()
                        for img_url in raw.image_urls:
                            db.add(ListingImage(listing_id=listing.id, source_url=img_url))
                        new_count += 1
                db.commit()
                logger_.info(f"WG-Gesucht scraping complete: {new_count} new listings saved.")
            finally:
                db.close()

    except Exception as e:
        logger_.error(f"Scraping failed: {e}")
