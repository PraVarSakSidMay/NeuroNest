"""LLM Router — OpenRouter → OpenAI → Groq → Gemini fallback"""
import logging
from langchain_core.messages import BaseMessage
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def invoke_with_fallback(
    messages: list[BaseMessage],
    temperature: float = 0.85,
    max_tokens: int = 800,
    emotion_value: str = "neutral",
    user_message: str = "",
    conversation_history: list = None,
) -> str:
    providers = _build_provider_list(temperature, max_tokens)
    last_error = None
    for name, llm in providers:
        try:
            logger.info(f"Trying LLM: {name}")
            response = await llm.ainvoke(messages)
            logger.info(f"Success: {name}")
            return response.content
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            last_error = e
            continue
    logger.error(f"All LLMs failed: {last_error}.")
    return "I am currently experiencing connectivity issues and cannot reach my AI service. Please check the API keys or try again in a moment."


def _build_provider_list(temperature: float, max_tokens: int) -> list[tuple[str, object]]:
    providers = []
    if settings.openrouter_api_key and "your_" not in settings.openrouter_api_key:
        try:
            from langchain_openai import ChatOpenAI
            providers.append(("OpenRouter", ChatOpenAI(
                model=settings.openrouter_model, temperature=temperature,
                api_key=settings.openrouter_api_key, max_tokens=max_tokens,
                base_url="https://openrouter.ai/api/v1"
            )))
        except Exception as e:
            logger.warning(f"OpenRouter init failed: {e}")
    if settings.openai_api_key and "your_" not in settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            providers.append(("OpenAI GPT-4o", ChatOpenAI(
                model=settings.openai_model, temperature=temperature,
                api_key=settings.openai_api_key, max_tokens=max_tokens,
            )))
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")
    if settings.groq_api_key and "your_" not in settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            providers.append(("Groq Llama-3.3-70B", ChatGroq(
                model=settings.groq_model, temperature=temperature,
                api_key=settings.groq_api_key, max_tokens=max_tokens,
            )))
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")
    if settings.gemini_api_key and "your_" not in settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            providers.append(("Gemini 1.5 Flash", ChatGoogleGenerativeAI(
                model=settings.gemini_model, temperature=temperature,
                google_api_key=settings.gemini_api_key, max_output_tokens=max_tokens,
            )))
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")
    if not providers:
        logger.warning("No LLM providers configured — using local fallback only.")
    return providers
