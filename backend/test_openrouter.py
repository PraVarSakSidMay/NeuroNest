import asyncio
import logging
from app.config import get_settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO)
settings = get_settings()

async def test():
    print(f"Key: {settings.openrouter_api_key[:10]}...")
    print(f"Model: {settings.openrouter_model}")
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        max_tokens=100
    )
    try:
        response = await llm.ainvoke([HumanMessage(content="Hello")])
        print("Success:", response.content)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
