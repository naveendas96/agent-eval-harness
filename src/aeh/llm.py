"""Pluggable LLM layer. Select with LLM_PROVIDER=mock|ollama|openai|anthropic.

The mock provider is deterministic so tests and demos run with no key or model.
"""
from __future__ import annotations

import os
from typing import Callable, Protocol

import httpx


class LLM(Protocol):
    def complete(self, prompt: str, system: str = "") -> str: ...


class MockLLM:
    """Deterministic LLM. An optional handler maps prompt -> response."""

    def __init__(self, handler: Callable[[str, str], str] | None = None) -> None:
        self.handler = handler
        self.calls: list[str] = []

    def complete(self, prompt: str, system: str = "") -> str:
        self.calls.append(prompt)
        if self.handler:
            return self.handler(prompt, system)
        return "MOCK: " + prompt[:200]


class OllamaLLM:
    def __init__(self) -> None:
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama3.2:1b")

    def complete(self, prompt: str, system: str = "") -> str:
        r = httpx.post(f"{self.url}/api/generate", timeout=120, json={
            "model": self.model, "prompt": prompt, "system": system, "stream": False})
        r.raise_for_status()
        return str(r.json()["response"])


class OpenAILLM:
    def __init__(self) -> None:
        self.key = os.environ["OPENAI_API_KEY"]
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def complete(self, prompt: str, system: str = "") -> str:
        r = httpx.post("https://api.openai.com/v1/chat/completions", timeout=120,
                       headers={"Authorization": f"Bearer {self.key}"},
                       json={"model": self.model, "temperature": 0, "messages": [
                           {"role": "system", "content": system},
                           {"role": "user", "content": prompt}]})
        r.raise_for_status()
        return str(r.json()["choices"][0]["message"]["content"])


class AnthropicLLM:
    def __init__(self) -> None:
        self.key = os.environ["ANTHROPIC_API_KEY"]
        self.model = os.getenv("LLM_MODEL", "claude-3-5-haiku-latest")

    def complete(self, prompt: str, system: str = "") -> str:
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=120,
                       headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"},
                       json={"model": self.model, "max_tokens": 1500, "temperature": 0,
                             "system": system,
                             "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return str(r.json()["content"][0]["text"])


def get_llm(handler: Callable[[str, str], str] | None = None) -> LLM:
    p = os.getenv("LLM_PROVIDER", "mock").lower()
    if p == "ollama":
        return OllamaLLM()
    if p == "openai":
        return OpenAILLM()
    if p == "anthropic":
        return AnthropicLLM()
    return MockLLM(handler)
