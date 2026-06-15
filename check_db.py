import asyncio
import sys
import os

# Add the 'backend' directory to the system path to allow importing internal modules
# We use the script's location as a reference for more robust path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from infrastructure.mongodb_client import init_db, get_db
from core.config import settings

async def check_db():
    """
    Diagnostic script to verify MongoDB connection and inspect stored data.
    """
    print(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    try:
        # Initialize the database connection
        await init_db()
        db = get_db()
        
        # Count documents in core collections to verify storage is working
        interactions_count = await db["interactions"].count_documents({})
        sessions_count = await db["sessions"].count_documents({})
        users_count = await db["users"].count_documents({})
        
        print("\n--- DB Status ---")
        print(f"Interactions: {interactions_count}")
        print(f"Sessions:     {sessions_count}")
        print(f"Users:        {users_count}")
        
        if interactions_count > 0:
            print("\nRecent interactions:")
            # Fetch the 3 most recent interactions to verify content and RL data
            cursor = db["interactions"].find().sort("created_at", -1).limit(3)
            async for doc in cursor:
                print(f"- [{doc.get('created_at')}] Transcript: {doc.get('transcript')[:50]}...")
                print(f"  Response: {doc.get('response_text', 'N/A')[:50]}...")
                print(f"  Feedback: {doc.get('feedback_score')} | Persona: {doc.get('applied_persona')}")
        else:
            print("\nNo interactions found in database yet. Try having a conversation first!")
            
    except Exception as e:
        print(f"\n❌ Error connecting to DB: {e}")

if __name__ == "__main__":
    # Run the async diagnostic
    asyncio.run(check_db())
