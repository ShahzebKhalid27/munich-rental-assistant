"""Shared Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class ListingBase(BaseModel):
    title: str
    description: str
    price_total: float | None = None
    price_cold: float | None = None
    size_sqm: float | None = None
    address: str | None = None
    city: str | None = None
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ListingCreate(ListingBase):
    external_id: str | None = None
    source: str = "manual"


class ListingResponse(ListingBase):
    id: int
    external_id: str | None
    source: str
    available_from: datetime | None
    image_urls: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    results: list[ListingResponse]
    total: int
    offset: int
    limit: int


# ── User schemas ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Search Profile schemas ────────────────────────────────────────────────────

class SearchProfileBase(BaseModel):
    name: str
    city: str = "München"
    price_max: float | None = None
    price_min: float | None = None
    size_min_sqm: float | None = None
    size_max_sqm: float | None = None
    wg_type: str | None = None
    preferred_districts: str | None = None  # JSON list as string
    commute_lat: float | None = None
    commute_lng: float | None = None
    commute_max_minutes: int | None = None
    auto_apply_enabled: bool = False


class SearchProfileCreate(SearchProfileBase):
    pass


class SearchProfileResponse(SearchProfileBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
