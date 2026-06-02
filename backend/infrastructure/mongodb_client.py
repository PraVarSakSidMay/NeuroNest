"""MongoDB Motor async client — singleton used by all repositories."""
from __future__ import annotations

from typing import Optional
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING

from core.config import settings
from core.logger import logger

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    """Return (or lazily create) the shared Motor client."""
    global _client
    if _client is None:
        uri = settings.MONGODB_URI or "mongodb://localhost:27017"
        # serverSelectionTimeoutMS prevents hanging indefinitely when Mongo is unreachable
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
        )
        logger.info(f"MongoDB client created — URI: {uri}")
    return _client


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Return the application database handle."""
    global _db
    if _db is None:
        db_name = settings.MONGODB_DB or "neuronest"
        _db = get_client()[db_name]
        logger.info(f"MongoDB database selected: {db_name}")
    return _db


async def init_db() -> None:
    """Create collections and indexes on startup (idempotent)."""
    db = get_db()
    try:
        # Ping the server first to catch connection errors early
        await db.command("ping")

        # sessions — index on user_id + started_at for fast lookups
        await db["sessions"].create_index([("user_id", ASCENDING), ("started_at", DESCENDING)])

        # interactions — index on session_id and user_id + created_at
        await db["interactions"].create_index([("session_id", ASCENDING), ("created_at", DESCENDING)])
        await db["interactions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        logger.info("MongoDB indexes ensured.")
    except Exception as e:
        logger.error(
            f"MongoDB init failed — is MongoDB running? URI: {settings.MONGODB_URI}\nError: {e}"
        )
        # Don't raise — allow server to start; DB calls will fail on demand with clear errors.


async def close_db() -> None:
    """Close the Motor client on shutdown."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB client closed.")
