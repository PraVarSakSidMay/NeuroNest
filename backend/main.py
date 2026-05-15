"""
NeuroNest Journal API — FastAPI application entry point.

Loads environment variables from .env, configures CORS, and mounts the
journal router.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env before any module that reads environment variables is imported
load_dotenv()

from routers.journal import router as journal_router  # noqa: E402

app = FastAPI(title="NeuroNest Journal API")

# ── CORS ──────────────────────────────────────────────────────────────────
# DEMO MODE: Allow all origins for easier testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in demo mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(journal_router, prefix="/journal")
