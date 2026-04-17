"""
Listings API v1 — CRUD + scraping trigger + filtering.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from ...db import get_db
from ...models import Listing, ListingImage, SearchProfile
from ..schemas import ListingCreate, ListingResponse, ListingListResponse
from ...services.scraping.wg_gesucht import fetch_multiple_pages, WGSearchParams


router = APIRouter()


# ── GET /api/v1/listings ──────────────────────────────────────────────────────

@router.get("/", response_model=ListingListResponse)
async def list_listings(
    db: Annotated[Session, Depends(get_db)],
    city: str | None = Query(None, description="Filter by city (default: München)"),
    district: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_size: float | None = Query(None, ge=0),
    max_size: float | None = Query(None),
    wg_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ListingListResponse:
    """
    List listings with optional filters.

    Returns paginated results with total count.
    """

    query = select(Listing).options(joinedload(Listing.images))

    if city:
        query = query.where(Listing.city == city)
    else:
        query = query.where(Listing.city == "München")  # default city

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
        # Heuristic: listings with title containing "Zimmer", "WG", "Room" are WG
        query = query.where(Listing.title.ilike("%zimmer%") | Listing.title.ilike("%wg%") | Listing.title.ilike("%room%"))

    # Count total
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

    total = db.scalar(count_q) or 0

    # Apply pagination + order
    query = query.order_by(Listing.created_at.desc()).offset(offset).limit(limit)

    results = db.scalars(query).unique().all()

    listings = [
        ListingResponse(
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
        for listing in results
    ]

    return ListingListResponse(results=listings, total=total, offset=offset, limit=limit)


# ── GET /api/v1/listings/{id} ─────────────────────────────────────────────────

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ListingResponse:
    listing = db.scalars(
        select(Listing).options(joinedload(Listing.images)).where(Listing.id == listing_id)
    ).first()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")


# ── GET /api/v1/listings/match/{profile_id} ──────────────────────────────────

@router.get("/match/{profile_id}")
async def match_listings(
    profile_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
    use_llm: bool = Query(False, description="Enable LLM-powered scoring (slower, more accurate)"),
) -> dict:
    """
    Get top-matching listings for a user's search profile.

    Phase 1: Rule-based hard filters + price/size proximity scoring.
    Phase 2+: LLM adds Lage, description quality, and vibe matching.

    Set use_llm=true for richer scoring (costs API calls).
    """
    profile = db.scalars(
        select(SearchProfile).where(SearchProfile.id == profile_id, SearchProfile.is_active == True)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")

    # Fetch active listings (most recent first)
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


# ── POST /api/v1/listings/scrape ──────────────────────────────────────────────

@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    city: str = "München",
    district: str | None = None,
    max_price: int | None = None,
    min_size_sqm: float | None = None,
    pages: int = Query(2, ge=1, le=10),
) -> dict:
    """
    Trigger a WG-Gesucht scrape job in the background.

    Returns immediately with job status. Listings are stored in DB.
    Use GET /api/v1/listings to retrieve results after scraping.
    """
    params = WGSearchParams(
        city=city,
        district=district,
        max_price=max_price,
        min_size_sqm=min_size_sqm,
        wg_only=True,
    )

    background_tasks.add_task(_scrape_and_save_task, params, pages)

    return {
        "status": "started",
        "message": f"Scraping started for {city}" + (f" ({district})" if district else ""),
        "pages": pages,
        "check_results_at": "/api/v1/listings",
    }


async def _scrape_and_save_task(params: WGSearchParams, pages: int):
    """
    Background task: scrape WG-Gesucht and persist results to DB.
    """
    from ...db import SessionLocal
    from ...models import Listing, ListingImage

    logger_ = logging.getLogger(__name__)

    try:
        listings = await fetch_multiple_pages(params, pages=pages)

        db = SessionLocal()
        try:
            new_count = 0
            for wg in listings:
                # Check if already exists
                existing = db.scalars(
                    select(Listing).where(
                        Listing.external_id == wg.external_id,
                        Listing.source == "wg_gesucht",
                    )
                ).first()

                if existing:
                    # Update
                    existing.title = wg.title
                    existing.description = wg.description
                    existing.price_total = wg.price_total
                    existing.size_sqm = wg.size_sqm
                    existing.available_from = wg.available_from
                    existing.updated_at = datetime.utcnow()
                else:
                    # Insert
                    listing = Listing(
                        external_id=wg.external_id,
                        source="wg_gesucht",
                        title=wg.title,
                        description=wg.description,
                        price_total=wg.price_total,
                        price_cold=wg.price_cold,
                        size_sqm=wg.size_sqm,
                        address=wg.address,
                        city=wg.city or "München",
                        district=wg.district,
                        latitude=wg.latitude,
                        longitude=wg.longitude,
                        available_from=wg.available_from,
                    )
                    db.add(listing)
                    db.flush()

                    # Save images
                    for img_url in wg.image_urls:
                        img = ListingImage(
                            listing_id=listing.id,
                            source_url=img_url,
                        )
                        db.add(img)

                    new_count += 1

            db.commit()
            logger_.info(f"Scraping complete: {new_count} new listings saved.")

        finally:
            db.close()

    except Exception as e:
        logger_.error(f"Scraping failed: {e}")


import logging

from ...services.matching import get_top_matches, is_match_hard
