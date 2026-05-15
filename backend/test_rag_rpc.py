import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load from current dir or parent backend dir
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("backend/.env"):
    load_dotenv("backend/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase: Client = create_client(url, key)

USER_ID = "00000000-0000-0000-0000-000000000000"

async def test_rag_functionality():
    print(f"Testing RAG Functionality...")
    
    try:
        # 1. Test get_last_session_emotion
        print("\n1. Testing get_last_session_emotion RPC...")
        result = supabase.rpc(
            "get_last_session_emotion",
            {
                "lookup_user_id": USER_ID
            }
        ).execute()
        print(f"   Result: {result.data}")
        
        # 2. Test match_interactions
        print("\n2. Testing match_interactions RPC...")
        # Dummy embedding
        dummy_embedding = [0.1] * 1536
        match_result = supabase.rpc(
            "match_interactions",
            {
                "query_embedding": dummy_embedding,
                "match_user_id": USER_ID,
                "match_count": 5
            }
        ).execute()
        print(f"   Result count: {len(match_result.data) if match_result.data else 0}")
        if match_result.data:
            print(f"   Latest match similarity: {match_result.data[0].get('similarity')}")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rag_functionality())
