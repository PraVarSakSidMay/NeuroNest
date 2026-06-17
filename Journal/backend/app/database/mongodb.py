"""
MongoDB connection management using Motor async driver.

Provides a singleton database class and lifecycle functions
for connecting and disconnecting from MongoDB.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings


class Database:
    """Singleton container for the Motor async MongoDB client and database reference."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


database = Database()


def get_database() -> AsyncIOMotorDatabase:
    """Return the current MongoDB database reference.

    Returns:
        The configured AsyncIOMotorDatabase instance.

    Raises:
        RuntimeError: If the database has not been connected yet.
    """
    if database.db is None:
        raise RuntimeError("Database is not connected. Call connect_db() first.")
    return database.db


async def connect_db() -> None:
    """Establish a connection to MongoDB using the configured URI.

    Creates the Motor client and selects the configured database.
    """
    settings = get_settings()
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    database.db = database.client[settings.MONGODB_DATABASE]


async def close_db() -> None:
    """Close the MongoDB connection and clean up resources."""
    if database.client is not None:
        database.client.close()
        database.client = None
        database.db = None
