"""User & Auth API — register, login, profile management."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import User, SearchProfile
from ..schemas import UserCreate, UserResponse, SearchProfileCreate, SearchProfileResponse
from ...services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


# ── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Auth helpers ─────────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Dependency: extract + validate JWT, return the User."""
    from ...services.auth import decode_token

    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.scalars(select(User).where(User.id == int(user_id))).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    existing = db.scalars(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = db.scalars(select(User).where(User.email == data.email)).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated.")

    token = create_access_token(
        {"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(days=7),
    )

    return LoginResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


# ── Search Profiles ────────────────────────────────────────────────────────────

@router.post("/me/profiles", response_model=SearchProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: SearchProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SearchProfile:
    import json
    profile = SearchProfile(
        user_id=user.id,
        name=data.name,
        city=data.city or "München",
        price_max=data.price_max,
        price_min=data.price_min,
        size_min_sqm=data.size_min_sqm,
        size_max_sqm=data.size_max_sqm,
        wg_type=data.wg_type,
        preferred_districts=(
            json.dumps(data.preferred_districts.split(","))
            if data.preferred_districts else None
        ),
        auto_apply_enabled=data.auto_apply_enabled,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/profiles", response_model=list[SearchProfileResponse])
async def list_profiles(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[SearchProfile]:
    return db.scalars(
        select(SearchProfile)
        .where(SearchProfile.user_id == user.id, SearchProfile.is_active == True)
        .order_by(SearchProfile.created_at.desc())
    ).all()


@router.delete("/me/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    profile = db.scalars(
        select(SearchProfile).where(
            SearchProfile.id == profile_id,
            SearchProfile.user_id == user.id,
        )
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.is_active = False
    db.commit()
