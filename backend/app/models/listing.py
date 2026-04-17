from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # External reference on the source portal (e.g. WG-Gesucht id)
    external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # e.g. "wg_gesucht"

    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)

    price_total: Mapped[float | None] = mapped_column(Float)
    price_cold: Mapped[float | None] = mapped_column(Float)
    size_sqm: Mapped[float | None] = mapped_column(Float)

    address: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(128), index=True)
    district: Mapped[str | None] = mapped_column(String(128), index=True)

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    available_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    images: Mapped[list["ListingImage"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)

    source_url: Mapped[str | None] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    listing: Mapped[Listing] = relationship(back_populates="images")
