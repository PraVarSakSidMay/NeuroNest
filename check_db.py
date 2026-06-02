
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from infrastructure.mongodb_client import init_db, get_db
from core.config import settings

async def check_db():
    print(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    try:
        await init_db()
        db = get_db()
        
        interactions_count = await db["interactions"].count_documents({})
        sessions_count = await db["sessions"].count_documents({})
        users_count = await db["users"].count_documents({})
        
        print("\n--- DB Status ---")
        print(f"Interactions: {interactions_count}")
        print(f"Sessions:     {sessions_count}")
        print(f"Users:        {users_count}")
        
        if interactions_count > 0:
            print("\nRecent interactions:")
            cursor = db["interactions"].find().sort("created_at", -1).limit(3)
            async for doc in cursor:
                print(f"- [{doc.get('created_at')}] Transcript: {doc.get('transcript')[:50]}...")
                print(f"  Response: {doc.get('response_text')[:50]}...")
                print(f"  Feedback: {doc.get('feedback_score')} | Persona: {doc.get('applied_persona')}")
        else:
            print("\nNo interactions found in database yet.")
            
    except Exception as e:
        print(f"\nError connecting to DB: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
