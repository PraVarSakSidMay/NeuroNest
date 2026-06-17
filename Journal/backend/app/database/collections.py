"""
MongoDB collection references and index creation.

Provides helper functions to access specific collections
and to create the required indexes on startup.
"""

from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo

from app.database.mongodb import get_database


def get_journal_collection() -> AsyncIOMotorCollection:
    """Return a reference to the 'journal_entries' collection.

    Returns:
        The journal_entries AsyncIOMotorCollection.
    """
    db = get_database()
    return db["journal_entries"]


def get_summaries_collection() -> AsyncIOMotorCollection:
    """Return a reference to the 'emotional_summaries' collection.

    Returns:
        The emotional_summaries AsyncIOMotorCollection.
    """
    db = get_database()
    return db["emotional_summaries"]


async def create_indexes() -> None:
    """Create database indexes for optimal query performance.

    Creates the following indexes:
    - journal_entries: user_id (asc), created_at (desc), compound (user_id + created_at)
    - emotional_summaries: user_id (asc), created_at (desc)
    """
    journal_col = get_journal_collection()
    await journal_col.create_index([("user_id", pymongo.ASCENDING)])
    await journal_col.create_index([("created_at", pymongo.DESCENDING)])
    await journal_col.create_index(
        [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)]
    )

    summaries_col = get_summaries_collection()
    await summaries_col.create_index([("user_id", pymongo.ASCENDING)])
    await summaries_col.create_index([("created_at", pymongo.DESCENDING)])
