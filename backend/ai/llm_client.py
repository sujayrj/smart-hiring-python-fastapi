"""Provider-agnostic LLM client.

Guardrails (per spec):
- Every response is validated against a Pydantic schema before use.
- Invalid JSON -> retry exactly once with a correction instruction.
- Still invalid -> controlled LLMError (never an uncontrolled retry loop).
"""

from __future__ import annotations

import json
import re
from typing import Optional, Protocol, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from config import settings

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Controlled application error raised for unrecoverable LLM failures."""


class Provider(Protocol):
    name: str

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class CallableProvider:
    """Test/DI provider: returns whatever the callable yields."""

    def __init__(self, fn, name: str = "callable"):
        self._fn = fn
        self.name = name

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._fn(system_prompt, user_prompt)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        return fence.group(1)
    # tolerate prose before/after a JSON object
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


class LLMClient:
    def __init__(self, provider: Optional[Provider]):
        self.provider = provider

    @property
    def is_mock(self) -> bool:
        return self.provider is None

    @property
    def provider_name(self) -> str:
        return self.provider.name if self.provider else "mock"

    def complete_json(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        if self.provider is None:
            raise LLMError("No LLM provider configured")

        attempts = 2  # initial + exactly one retry
        last_error: Exception | None = None
        prompt = user_prompt

        for attempt in range(attempts):
            try:
                raw = self.provider.complete(system_prompt, prompt)
            except httpx.HTTPError as exc:
                raise LLMError(f"LLM provider request failed: {exc}") from exc

            try:
                data = json.loads(_strip_code_fences(raw))
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt == 0:
                    prompt = (
                        f"{user_prompt}\n\nYour previous response was invalid "
                        f"({exc.__class__.__name__}). Respond with ONLY valid JSON that "
                        f"strictly matches the requested schema. No prose, no markdown."
                    )
                    continue

        raise LLMError(f"LLM returned invalid structured output after retry: {last_error}")


def build_client() -> LLMClient:
    """Factory: real provider when configured, otherwise mock (offline)."""
    provider = settings.llm_provider.lower()
    if provider == "openai" and settings.llm_api_key:
        return LLMClient(
            OpenAIProvider(
                settings.llm_api_key, settings.llm_model, settings.llm_base_url,
                settings.llm_timeout_seconds,
            )
        )
    if provider == "anthropic" and settings.llm_api_key:
        return LLMClient(
            AnthropicProvider(settings.llm_api_key, settings.llm_model, settings.llm_timeout_seconds)
        )
    return LLMClient(None)
