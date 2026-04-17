from pathlib import Path

from ..core.config import get_settings


settings = get_settings()


def get_listing_image_path(listing_id: int, filename: str) -> Path:
    """Build local filesystem path for a listing image.

    In Produktion kann diese Logik durch ein S3-/Object-Storage-Backend ersetzt werden,
    die Signaturen/URLs generiert, aber die DB-Schnittstelle bleibt gleich.
    """

    root = Path(settings.media_root) / "listings" / str(listing_id)
    root.mkdir(parents=True, exist_ok=True)
    return root / filename


def get_listing_image_url(listing_id: int, filename: str) -> str:
    """Public URL für das Frontend.

    Für lokale Entwicklung kann das z.B. über einen `/media`-Static-Endpoint von FastAPI
    ausgeliefert werden. Später: CDN/S3-URL.
    """

    return f"/media/listings/{listing_id}/{filename}"
