"""
Matching service — decides which listings match which search profiles.

Strategy:
- Phase 1: Rule-based hard filters (price, size, district, WG-type).
- Phase 2+: LLM-powered soft scoring (Lage, text similarity, vibe matching).

The matching engine is called:
1. When new listings are scraped → score against all active profiles → notify user
2. When a user loads their dashboard → show top matches with scores
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Listing, SearchProfile

logger = logging.getLogger(__name__)

# ── Hard filter (Phase 1 — deterministic) ───────────────────────────────────

def is_match_hard(listing: "Listing", profile: "SearchProfile") -> tuple[bool, str]:
    """
    Apply hard filters. Returns (matched, reason_if_not).
    These are all-or-nothing — no partial credit.
    """

    # Price check
    if profile.price_max is not None and listing.price_total is not None:
        if listing.price_total > profile.price_max:
            return False, f"Preis {listing.price_total}€ über Limit {profile.price_max}€"

    if profile.price_min is not None and listing.price_total is not None:
        if listing.price_total < profile.price_min:
            return False, f"Preis {listing.price_total}€ unter Minimum {profile.price_min}€"

    # Size check
    if profile.size_min_sqm is not None and listing.size_sqm is not None:
        if listing.size_sqm < profile.size_min_sqm:
            return False, f"Größe {listing.size_sqm}m² unter Minimum {profile.size_min_sqm}m²"

    if profile.size_max_sqm is not None and listing.size_sqm is not None:
        if listing.size_sqm > profile.size_max_sqm:
            return False, f"Größe {listing.size_sqm}m² über Maximum {profile.size_max_sqm}m²"

    # District check
    if profile.preferred_districts and listing.district:
        import json
        try:
            districts = json.loads(profile.preferred_districts)
            if isinstance(districts, list) and len(districts) > 0:
                if listing.district not in districts:
                    return False, f"Stadtteil {listing.district} nicht in Wunschvierteln"
        except json.JSONDecodeError:
            pass  # skip district filter if malformed

    # WG-type check (if profile specifies a type)
    if profile.wg_type and profile.wg_type != "all":
        title_lower = (listing.title or "").lower()
        desc_lower = (listing.description or "").lower()
        combined = title_lower + " " + desc_lower

        if profile.wg_type == "wg":
            wg_indicators = ["zimmer", "wg-", "room", "möbliertes zimmer", "wg-zimmer"]
            if not any(ind in combined for ind in wg_indicators):
                return False, "Kein WG-Zimmer-Inserat"

        elif profile.wg_type == "studio":
            studio_indicators = ["studio", "appartment", "1-zimmer", "1 zimmer"]
            if not any(ind in combined for ind in studio_indicators):
                return False, "Kein Studio/Apartment-Inserat"

    return True, "OK"


# ── Score computation (Phase 2 — LLM-powered) ────────────────────────────────

async def compute_match_score(
    listing: "Listing",
    profile: "SearchProfile",
    use_llm: bool = False,
) -> tuple[float, str]:
    """
    Compute a 0.0–1.0 match score with explanation.

    Phase 1: Purely rule-based price proximity score.
    Phase 2+: LLM adds Lage, vibe, and description quality scoring.

    Returns (score, explanation_str).
    """
    from .llm import score_match

    # ── Phase 1: Rule-based price proximity score ──
    price_score = 1.0
    if profile.price_max and listing.price_total:
        # Linear score: at limit = 0.5, 20% under limit = 1.0
        ratio = listing.price_total / profile.price_max
        price_score = max(0.0, min(1.0, 2.0 - ratio * 1.5))

    size_score = 1.0
    if profile.size_min_sqm and listing.size_sqm:
        # Closer to ideal range → higher score
        # We treat size_min_sqm as the sweet spot
        ratio = listing.size_sqm / profile.size_min_sqm
        size_score = max(0.0, min(1.0, ratio))

    # Simple weighted average for Phase 1
    rule_score = (price_score * 0.6) + (size_score * 0.4)
    explanation = (
        f"Preis-Score: {price_score:.2f} "
        f"(Limit: {profile.price_max}€, Inserat: {listing.price_total}€), "
        f"Größen-Score: {size_score:.2f}"
    )

    # ── Phase 2: LLM enhancement ──
    if use_llm:
        llm_score = await score_match(
            listing_data={
                "title": listing.title,
                "description": listing.description,
                "price_total": listing.price_total,
                "size_sqm": listing.size_sqm,
                "district": listing.district,
                "address": listing.address,
                "wg_type": profile.wg_type,
                "available_from": str(listing.available_from) if listing.available_from else None,
            },
            profile_data={
                "price_max": profile.price_max,
                "price_min": profile.price_min,
                "size_min_sqm": profile.size_min_sqm,
                "size_max_sqm": profile.size_max_sqm,
                "preferred_districts": profile.preferred_districts,
                "wg_type": profile.wg_type,
            },
        )

        if llm_score:
            # Blend rule score (40%) with LLM score (60%)
            final_score = (rule_score * 0.4) + (llm_score.score * 0.6)
            explanation = f"LLM: {llm_score.explanation}"
            return final_score, explanation

    return rule_score, explanation


# ── Bulk matching ─────────────────────────────────────────────────────────────

async def get_top_matches(
    listings: list["Listing"],
    profile: "SearchProfile",
    limit: int = 10,
    use_llm: bool = False,
) -> list[tuple["Listing", float, str]]:
    """
    Return the best-matching listings for a search profile,
    sorted by match score descending.

    Returns list of (listing, score, explanation) tuples.
    """
    results: list[tuple["Listing", float, str]] = []

    for listing in listings:
        matched, reason = is_match_hard(listing, profile)
        if not matched:
            continue

        score, explanation = await compute_match_score(listing, profile, use_llm=use_llm)
        if score > 0.3:  # minimum threshold
            results.append((listing, score, explanation))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:limit]
