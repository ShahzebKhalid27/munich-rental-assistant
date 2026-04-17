"""User & SearchProfile API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import User, SearchProfile
from ..schemas import UserCreate, UserResponse, SearchProfileCreate, SearchProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


# ── User CRUD ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    """Register a new user account."""

    # Check duplicate email
    existing = db.scalars(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        email=data.email,
        hashed_password=data.password,  # TODO: hash before storage!
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    # TODO: wire in real auth (JWT/OAuth) — placeholder for now
    user_id: int = 1,
) -> User:
    user = db.scalars(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Search Profiles ────────────────────────────────────────────────────────────

@router.post("/me/profiles", response_model=SearchProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_search_profile(
    data: SearchProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: int = 1,  # TODO: replace with real auth
) -> SearchProfile:
    profile = SearchProfile(user_id=user_id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/profiles", response_model=list[SearchProfileResponse])
async def list_search_profiles(
    db: Annotated[Session, Depends(get_db)],
    user_id: int = 1,
) -> list[SearchProfile]:
    return db.scalars(
        select(SearchProfile)
        .where(SearchProfile.user_id == user_id, SearchProfile.is_active == True)
        .order_by(SearchProfile.created_at.desc())
    ).all()


@router.delete("/me/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search_profile(
    profile_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_id: int = 1,
):
    profile = db.scalars(
        select(SearchProfile)
        .where(SearchProfile.id == profile_id, SearchProfile.user_id == user_id)
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.is_active = False
    db.commit()
