import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin async client for OpenAI Chat Completions and Google Gemini."""

    @staticmethod
    def resolve_provider() -> str:
        pref = (settings.AI_PROVIDER or "auto").lower()
        if pref == "local":
            return "local"
        if pref == "openai" and settings.OPENAI_API_KEY:
            return "openai"
        if pref == "gemini" and settings.GEMINI_API_KEY:
            return "gemini"
        if pref == "auto":
            if settings.OPENAI_API_KEY:
                return "openai"
            if settings.GEMINI_API_KEY:
                return "gemini"
        return "local"

    @staticmethod
    async def complete(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 1200,
    ) -> tuple[str, str]:
        provider = LLMClient.resolve_provider()
        if provider == "openai":
            try:
                text = await LLMClient._openai_complete(
                    system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
                )
                return text, "openai"
            except Exception as exc:
                logger.warning("OpenAI request failed: %s", exc)
                if settings.GEMINI_API_KEY:
                    try:
                        text = await LLMClient._gemini_complete(
                            system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
                        )
                        return text, "gemini"
                    except Exception as gem_exc:
                        logger.warning("Gemini fallback failed: %s", gem_exc)
        elif provider == "gemini":
            try:
                text = await LLMClient._gemini_complete(
                    system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
                )
                return text, "gemini"
            except Exception as exc:
                logger.warning("Gemini request failed: %s", exc)
                if settings.OPENAI_API_KEY:
                    try:
                        text = await LLMClient._openai_complete(
                            system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
                        )
                        return text, "openai"
                    except Exception as oai_exc:
                        logger.warning("OpenAI fallback failed: %s", oai_exc)
        raise RuntimeError("no_llm_available")

    @staticmethod
    async def _openai_complete(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    async def _gemini_complete(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        model = settings.GEMINI_MODEL
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={settings.GEMINI_API_KEY}"
        )
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        payload = {
            "contents": [{"parts": [{"text": combined}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts") or []
        if not parts:
            raise RuntimeError("Gemini returned empty content")
        return parts[0].get("text", "").strip()
