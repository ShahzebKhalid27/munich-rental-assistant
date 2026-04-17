from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(256))
    full_name: Mapped[str | None] = mapped_column(String(256))

    # Commute target (e.g. TUM main campus)
    commute_lat: Mapped[float | None] = mapped_column(Float)
    commute_lng: Mapped[float | None] = mapped_column(Float)
    commute_max_minutes: Mapped[int | None] = mapped_column(Integer)  # max travel time in minutes

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    search_profiles: Mapped[list["SearchProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SearchProfile(Base):
    __tablename__ = "search_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(128))  # e.g. "Mein WG-Filter"
    city: Mapped[str] = mapped_column(String(64), default="München")

    # Budget
    price_max: Mapped[float | None] = mapped_column(Float)
    price_min: Mapped[float | None] = mapped_column(Float)

    # Size
    size_min_sqm: Mapped[float | None] = mapped_column(Float)
    size_max_sqm: Mapped[float | None] = mapped_column(Float)

    # WG type: "wg", "studio", "apartment", null = all
    wg_type: Mapped[str | None] = mapped_column(String(32))

    # Preferred districts (list as comma-separated or JSON in DB)
    preferred_districts: Mapped[str | None] = mapped_column(Text)  # JSON list stored as text

    # Commute overrides (if different from user default)
    commute_lat: Mapped[float | None] = mapped_column(Float)
    commute_lng: Mapped[float | None] = mapped_column(Float)
    commute_max_minutes: Mapped[int | None] = mapped_column(Integer)

    # Auto-apply enabled?
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship(back_populates="search_profiles")
