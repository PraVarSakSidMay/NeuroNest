"""
AI Reflection service using OpenRouter API.

Makes async HTTP calls to OpenRouter's chat completions endpoint
to generate empathetic emotional reflections from journal entries.
"""

import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AIReflectionService:
    """Service for generating AI-powered emotional reflections.

    Uses httpx.AsyncClient to call the OpenRouter chat completions API
    with a carefully crafted system prompt for empathetic analysis.
    """

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    SYSTEM_PROMPT = (
        "You are an empathetic emotional reflection assistant. "
        "Analyze journal entries and provide supportive observations, "
        "emotional patterns, positive insights, and growth suggestions. "
        "Never provide medical diagnoses.\n\n"
        "You MUST respond with valid JSON in this exact format:\n"
        "{\n"
        '  "summary": "An overall emotional summary of the journal entries",\n'
        '  "emotional_patterns": ["pattern 1", "pattern 2"],\n'
        '  "positive_observations": ["observation 1", "observation 2"],\n'
        '  "gentle_insights": ["insight 1", "insight 2"],\n'
        '  "growth_suggestions": ["suggestion 1", "suggestion 2"]\n'
        "}\n\n"
        "Provide thoughtful, warm, and encouraging analysis. "
        "Each list should contain 2-5 items."
    )

    async def generate_reflection(self, entries_text: str) -> Dict[str, Any]:
        """Generate an emotional reflection from journal entry text.

        Sends the entries text to the OpenRouter API and parses the
        structured JSON response.

        Args:
            entries_text: Formatted text of journal entries to analyse.

        Returns:
            A dict with keys: summary, emotional_patterns,
            positive_observations, gentle_insights, growth_suggestions.
        """
        settings = get_settings()

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.FRONTEND_URL,
            "X-Title": "NeuroNest",
        }

        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Please analyze the following journal entries and provide "
                        "an empathetic emotional reflection:\n\n"
                        f"{entries_text}"
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.ENDPOINT, json=payload, headers=headers
                )
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Attempt to parse the JSON response
            parsed = json.loads(content)

            return {
                "summary": parsed.get("summary", ""),
                "emotional_patterns": parsed.get("emotional_patterns", []),
                "positive_observations": parsed.get("positive_observations", []),
                "gentle_insights": parsed.get("gentle_insights", []),
                "growth_suggestions": parsed.get("growth_suggestions", []),
            }

        except json.JSONDecodeError:
            # If JSON parsing fails, wrap raw text in summary field
            logger.warning("AI response was not valid JSON, using raw text as summary.")
            raw_text = content if "content" in dir() else "Unable to generate reflection."
            return {
                "summary": raw_text,
                "emotional_patterns": [],
                "positive_observations": [],
                "gentle_insights": [],
                "growth_suggestions": [],
            }

        except httpx.HTTPStatusError as exc:
            logger.error("OpenRouter API returned HTTP %s: %s", exc.response.status_code, exc.response.text)
            raise RuntimeError(
                f"AI service returned status {exc.response.status_code}"
            ) from exc

        except Exception as exc:
            logger.error("Failed to generate AI reflection: %s", exc)
            raise RuntimeError("Failed to generate AI reflection") from exc


# Module-level singleton
ai_reflection_service = AIReflectionService()
