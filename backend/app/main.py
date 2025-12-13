"""FastAPI application entry point."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api.routes import router


# Static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="TTB Label Verification API",
        description="API for verifying alcohol beverage labels using OCR and LLM",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure static directory exists
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "annotated").mkdir(parents=True, exist_ok=True)

    # Mount static files for serving annotated images
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include API routes
    app.include_router(router)

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "TTB Label Verification API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
