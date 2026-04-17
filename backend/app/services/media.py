"""
Media service — handles image storage and URL resolution.

Storage strategy:
- Phase 1: Images stay on source portal URLs (source_url) — no local download.
  Frontend shows them via portal URLs directly, or we proxy them.
- Phase 2+: Download to local storage or S3-compatible storage (for watermark,
  metadata strip, lazy loading). Controlled by MEDIA_STORAGE_BACKEND setting.

The DB always stores:
  - source_url  → original portal URL
  - storage_path → local file path or S3 key (null until downloaded)
"""

from __future__ import annotations

import logging
import hashlib
import httpx
from pathlib import Path

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Path helpers ──────────────────────────────────────────────────────────────

def get_listing_image_dir(listing_id: int) -> Path:
    """Base directory for all images of a listing."""
    root = Path(settings.media_root) / "listings" / str(listing_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_listing_image_path(listing_id: int, filename: str) -> Path:
    """Filesystem path for a specific listing image."""
    return get_listing_image_dir(listing_id) / filename


def filename_from_url(url: str) -> str:
    """Derive a safe local filename from a URL.

    Uses URL path hash as fallback to avoid encoding issues.
    Keeps original extension if detectable.
    """
    from urllib.parse import urlparse, unquote

    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Try to extract extension
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    for ext in allowed_exts:
        if ext in path.lower():
            # Take last occurrence to handle `photo.jpg?v=123`
            idx = path.lower().rfind(ext)
            name_part = path[idx - 1:idx + len(ext)]
            return name_part.lstrip("/")

    # Fallback: hash the full URL to a short hex name
    h = hashlib.sha1(url.encode()).hexdigest()[:12]
    return f"img_{h}.jpg"


def get_listing_image_url(listing_id: int, filename: str) -> str:
    """Backward-compatible alias for public_url_for."""
    return public_url_for(listing_id, filename)


def public_url_for(listing_id: int, filename: str) -> str:
    """Public URL for a stored listing image.

    In dev: served by FastAPI static mount at /media.
    In prod: replace with CloudFront/S3/CDN URL.
    """
    return f"/media/listings/{listing_id}/{filename}"


# ── Image download ─────────────────────────────────────────────────────────────

async def download_image(
    url: str,
    listing_id: int,
    client: httpx.AsyncClient | None = None,
    timeout: float = 20.0,
) -> tuple[str, Path] | None:
    """
    Download an image from a URL and save it to local media storage.

    Returns (filename, local_path) on success, None on failure.

    The caller is responsible for closing *client* if provided.
    """
    try:
        if client is None:
            client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

        response = await client.get(url)
        response.raise_for_status()

        content = response.content
        if len(content) < 1024:
            logger.warning(f"Image too small or empty: {url}")
            return None

        filename = filename_from_url(url)
        local_path = get_listing_image_path(listing_id, filename)

        local_path.write_bytes(content)
        logger.debug(f"Saved image: {local_path}")

        return filename, local_path

    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for image: {url}")
    except Exception as e:
        logger.warning(f"Failed to download image {url}: {e}")

    return None


async def download_listing_images(
    image_urls: list[str],
    listing_id: int,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """
    Download multiple images for a listing.

    Returns list of dicts with {source_url, storage_path, public_url}.
    Skips already-downloaded images (idempotent by filename).

    Set MEDIA_STORAGE_BACKEND=local or s3 to control where files go.
    """
    import asyncio

    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(20.0))

    results: list[dict] = []

    for url in image_urls:
        filename = filename_from_url(url)
        local_path = get_listing_image_path(listing_id, filename)

        if local_path.exists():
            # Already downloaded
            results.append({
                "source_url": url,
                "storage_path": str(local_path),
                "public_url": public_url_for(listing_id, filename),
            })
            continue

        downloaded = await download_image(url, listing_id, client=client)
        if downloaded:
            fn, path = downloaded
            results.append({
                "source_url": url,
                "storage_path": str(path),
                "public_url": public_url_for(listing_id, fn),
            })

        # Small delay to avoid hammering the same domain
        await asyncio.sleep(0.3)

    return results
