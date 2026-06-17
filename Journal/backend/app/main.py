"""
NeuroNest FastAPI Application Entry Point.

Configures the FastAPI app with lifespan management, CORS middleware,
route registration, global exception handling, and health-check endpoints.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.journal_routes import router as journal_router
from app.api.reflection_routes import router as reflection_router
from app.core.config import get_settings
from app.database.collections import create_indexes
from app.database.mongodb import close_db, connect_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Connects to MongoDB and creates indexes on startup,
    and closes the database connection on shutdown.
    """
    # Startup
    logger.info("Connecting to MongoDB...")
    await connect_db()
    logger.info("Creating database indexes...")
    await create_indexes()
    logger.info("NeuroNest API is ready.")

    yield

    # Shutdown
    logger.info("Closing MongoDB connection...")
    await close_db()
    logger.info("NeuroNest API has shut down.")


app = FastAPI(
    title="NeuroNest API",
    description=(
        "AI-powered reflective journal backend. "
        "Create encrypted journal entries and generate empathetic "
        "emotional reflections using advanced language models."
    ),
    version="1.0.0",
    lifespan=lifespan,
    strict_slashes=False,
)

# CORS middleware
settings = get_settings()
# Allow all origins for development (for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(journal_router)
app.include_router(reflection_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors.

    Logs the full exception and returns a generic 500 response
    to avoid leaking internal details.

    Args:
        request: The incoming HTTP request.
        exc: The unhandled exception.

    Returns:
        A JSON response with status 500.
    """
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        A dict indicating the service status.
    """
    return {"status": "healthy", "service": "NeuroNest API"}


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint returning API information.

    Returns:
        A dict with the API name, version, and documentation URL.
    """
    return {
        "name": "NeuroNest API",
        "version": "1.0.0",
        "description": "AI-powered reflective journal backend",
        "docs": "/docs",
    }
