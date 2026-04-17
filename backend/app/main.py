from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router as api_v1_router
from .db import engine, Base


def create_app() -> FastAPI:
    app = FastAPI(title="Munich Rental Assistant API", version="0.1.0")

    # CORS — allow Next.js frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # For early development only: auto-create tables on startup.
    # Später ersetzen wir das durch eine saubere Migrationsstrategie (Alembic).
    Base.metadata.create_all(bind=engine)

    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
