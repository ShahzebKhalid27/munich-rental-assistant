from fastapi import APIRouter

from . import listings, users

api_router = APIRouter()

api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
