import asyncio
from app.agents.wellness_agent import process_chat

async def test():
    print("Testing chat response...")
    response = await process_chat(
        user_message="I passed my final examination today, I am so relieved and happy!",
        conversation_history=[],
        session_id="test-session-123",
        user_id="test-user-123"
    )
    print("\n--- AI Response ---")
    print(response.response)
    print("\n--- Celebration Message ---")
    print(response.celebration_message)
    print("\n--- Special Action ---")
    print(response.special_action)
    
if __name__ == "__main__":
    asyncio.run(test())
