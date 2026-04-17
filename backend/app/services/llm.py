"""
LLM service — wraps OpenAI-compatible API for intelligent parsing tasks.

Used for:
1. Filling in missing data from listings (e.g. estimate Nebenkosten, Lage-Qualität)
2. Generating match scores between listings and search profiles
3. Spam/scam detection

The LLM is only called when data is missing or uncertain — not for every listing.
Fallsback gracefully if the LLM service is unavailable.
"""

from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")  # cheap + fast for structured tasks


# ── Request/Response ─────────────────────────────────────────────────────────

class LLMMessage(BaseModel):
    role: str
    content: str


class LLMChoice(BaseModel):
    message: LLMMessage


class LLMResponse(BaseModel):
    id: str
    choices: list[LLMChoice]
    usage: dict[str, int]


# ── Core client ────────────────────────────────────────────────────────────────

async def llm_complete(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str | None:
    """
    Send a prompt to the LLM API and return the text response.

    Returns None on failure (caller should handle gracefully).
    """
    if not LLM_API_KEY:
        logger.warning("LLM_API_KEY not set — skipping LLM call")
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        result = LLMResponse.model_validate(data)
        if result.choices:
            return result.choices[0].message.content.strip()
        return None

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM HTTP error {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")

    return None


# ── Listing enrichment ─────────────────────────────────────────────────────────

@dataclass
class ListingEnrichment:
    """Structured enrichment data for a listing."""
    missing_fields: list[str]
    estimated_nebkosten: float | None       # Estimated monthly additional costs (Betriebskosten)
    Lage_Bewertung: str                     # "gut", "mittel", "schlecht"
    Lage_Erlaeuterung: str                   # Short explanation
    is_suspicious: bool
    suspicion_reasons: list[str]


SYSTEM_PROMPT_ENRICH = """Du bist ein erfahrener Münchner Immobilienanalyst.
Du bekommst ein Inserat mit teilweise fehlenden Daten.
Schätze die fehlenden Werte basierend auf dem Kontext.
Wenn das Inserat verdächtig aussieht (z.B. Vorkasse, unrealistische Preise, unspezifische Beschreibungen), markiere es als verdächtig.

Antworte NUR mit gültigem JSON im Format:
{
  "missing_fields": ["feld1", "feld2"],
  "estimated_nebkosten": 150.0,
  "lage_bewertung": "gut",
  "lage_erlaeuterung": "Nähe zur U-Bahn, ruhige Wohnlage",
  "is_suspicious": false,
  "suspicion_reasons": []
}
Keine Erklärungen außer dem JSON."""


async def enrich_listing(listing_data: dict[str, Any]) -> ListingEnrichment | None:
    """
    Call LLM to enrich a listing's missing data.

    listing_data: dict with keys like title, description, price_total, size_sqm,
                  address, district (some may be None/missing).
    """
    prompt = f"""Analysiere folgendes Münchner Wohnungsinserat und schätze fehlende Werte:

Titel: {listing_data.get("title", "N/A")}
Beschreibung: {listing_data.get("description", "N/A")}
Kaltmiete: {listing_data.get("price_total", "N/A")} €
Größe: {listing_data.get("size_sqm", "N/A")} m²
Adresse/Stadtteil: {listing_data.get("district", listing_data.get("address", "N/A"))}
Stadt: {listing_data.get("city", "München")}
"""

    response_text = await llm_complete(prompt, system=SYSTEM_PROMPT_ENRICH)
    if not response_text:
        return None

    try:
        # Strip markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed = json.loads(text)

        return ListingEnrichment(
            missing_fields=parsed.get("missing_fields", []),
            estimated_nebkosten=parsed.get("estimated_nebkosten"),
            Lage_Bewertung=parsed.get("lage_bewertung", "mittel"),
            Lage_Erlaeuterung=parsed.get("lage_erlaeuterung", ""),
            is_suspicious=parsed.get("is_suspicious", False),
            suspicion_reasons=parsed.get("suspicion_reasons", []),
        )

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM enrichment JSON: {e}\nResponse: {response_text[:200]}")
        return None


# ── Match scoring ─────────────────────────────────────────────────────────────

@dataclass
class MatchScore:
    score: float           # 0.0 – 1.0
    explanation: str       # human-readable explanation


SYSTEM_PROMPT_MATCH = """Du bist ein Münchner Wohnungssuch-Assistent.
Bewerte wie gut ein Inserat zu einem Suchprofil passt.
Berücksichtige: Preis, Größe, Lage, WG-Typ, Verfügbarkeit.

Antworte NUR mit gültigem JSON:
{
  "score": 0.85,
  "explanation": "Perfekt: 720€ für 25m² in Maxvorstadt, U-Bahn in 5 Min zu Fuß."
}
Kein anderes Format."""


async def score_match(
    listing_data: dict[str, Any],
    profile_data: dict[str, Any],
) -> MatchScore | None:
    """
    Score how well a listing matches a user's search profile.
    Returns a MatchScore with 0.0–1.0 score and explanation.
    """
    prompt = f"""Bewerte wie gut dieses Inserat zum Suchprofil passt.

--- INSERAT ---
Titel: {listing_data.get("title", "N/A")}
Kaltmiete: {listing_data.get("price_total", "N/A")} €
Größe: {listing_data.get("size_sqm", "N/A")} m²
Stadtteil: {listing_data.get("district", "N/A")}
WG-Typ: {listing_data.get("wg_type", "N/A")}
Verfügbar ab: {listing_data.get("available_from", "N/A")}
Beschreibung: {listing_data.get("description", "N/A")[:300]}

--- SUCHE ---
Max. Preis: {profile_data.get("price_max", "N/A")} €
Min. Größe: {profile_data.get("size_min_sqm", "N/A")} m²
Bevorzugte Stadtteile: {profile_data.get("preferred_districts", "N/A")}
WG-Typ: {profile_data.get("wg_type", "N/A")}
"""

    response_text = await llm_complete(prompt, system=SYSTEM_PROMPT_MATCH)
    if not response_text:
        return None

    try:
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed = json.loads(text)

        return MatchScore(
            score=float(max(0.0, min(1.0, parsed.get("score", 0.0)))),
            explanation=parsed.get("explanation", ""),
        )

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse match score JSON: {e}")
        return None
