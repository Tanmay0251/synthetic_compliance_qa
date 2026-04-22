"""Model-agnostic LLM client with Anthropic/OpenAI/Stub backends."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Msg:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class Response:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    raw: Any = None


class LLMClient(Protocol):
    model: str

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
    ) -> Response: ...


class StubClient:
    """Reads canned responses from tests/fixtures/stub_responses.json keyed by `fixture_key`."""

    def __init__(self, fixture_path: Path | None = None, model: str = "stub") -> None:
        self.model = model
        self.fixture_path = fixture_path or (ROOT / "tests" / "fixtures" / "stub_responses.json")
        with self.fixture_path.open(encoding="utf-8") as f:
            self._fixtures: dict[str, dict[str, Any]] = json.load(f)

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        fixture_key: str = "gen_a_default",
    ) -> Response:
        fx = self._fixtures.get(fixture_key)
        if fx is None:
            raise KeyError(f"no stub fixture for key={fixture_key}")
        return Response(
            content=fx["content"],
            input_tokens=fx.get("input_tokens", 100),
            output_tokens=fx.get("output_tokens", 50),
            model=self.model,
        )


class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        from anthropic import Anthropic

        self.model = model
        self._client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Claude models that deprecate the `temperature` parameter (newer / extended-thinking era).
    _NO_TEMPERATURE_MODELS = {"claude-opus-4-7", "claude-opus-4-7[1m]"}

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        **_: Any,
    ) -> Response:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if self.model not in self._NO_TEMPERATURE_MODELS:
            kwargs["temperature"] = temperature
        try:
            resp = self._client.messages.create(**kwargs)
        except Exception as e:
            # Fallback: if the API complains about temperature at request time
            # (e.g. a model newly deprecated it), retry without.
            if "temperature" in str(e) and "temperature" in kwargs:
                kwargs.pop("temperature", None)
                resp = self._client.messages.create(**kwargs)
            else:
                raise
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return Response(
            content=text,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=self.model,
            raw=resp,
        )


class OpenAIClient:
    def __init__(self, model: str = "gpt-5") -> None:
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def complete(
        self,
        system: str,
        messages: list[Msg],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        response_format: str | None = None,
        seed: int | None = None,
        **_: Any,
    ) -> Response:
        msgs = [{"role": "system", "content": system}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        if seed is not None:
            kwargs["seed"] = seed
        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        return Response(
            content=text,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            model=self.model,
            raw=resp,
        )


def make_client(model: str) -> LLMClient:
    if model == "stub":
        return StubClient()
    if model.startswith("claude-"):
        return AnthropicClient(model=model)
    if model.startswith(("gpt-", "o")):
        return OpenAIClient(model=model)
    raise ValueError(f"unknown model family: {model}")
