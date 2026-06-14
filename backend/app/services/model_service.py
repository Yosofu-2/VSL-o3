"""Multi-provider LLM service with streaming support."""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator

import httpx


class LLMResponse:
    """Normalized response from any provider."""
    def __init__(self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def to_dict(self) -> dict:
        return {
            "choices": [{"message": {"content": self.content}}],
            "usage": {"prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens},
        }


class BaseProvider(ABC):
    """Abstract base for LLM provider adapters."""

    def __init__(self, api_base: str, api_key: str, model: str, temperature: float, max_tokens: int):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def build_url(self) -> str: ...

    @abstractmethod
    def build_headers(self) -> dict[str, str]: ...

    @abstractmethod
    def build_payload(self, messages: list[dict]) -> dict: ...

    @abstractmethod
    def parse_response(self, data: dict) -> LLMResponse: ...

    @abstractmethod
    def parse_stream_chunk(self, line: str) -> Optional[str]: ...

    async def chat_completion(self, messages: list[dict]) -> LLMResponse:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                self.build_url(),
                json=self.build_payload(messages),
                headers=self.build_headers(),
            )
            if resp.status_code == 401:
                raise RuntimeError("Authentication failed — check API key")
            if resp.status_code == 429:
                raise RuntimeError("Rate limited — reduce request frequency")
            resp.raise_for_status()
            data = resp.json()
        return self.parse_response(data)

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Yield text chunks for streaming responses."""
        payload = self.build_payload(messages)
        payload["stream"] = True
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                self.build_url(),
                json=payload,
                headers=self.build_headers(),
            ) as resp:
                if resp.status_code == 401:
                    raise RuntimeError("Authentication failed — check API key")
                if resp.status_code == 429:
                    raise RuntimeError("Rate limited — reduce request frequency")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    chunk = self.parse_stream_chunk(line)
                    if chunk:
                        yield chunk


class OpenAIProvider(BaseProvider):
    """OpenAI /v1/chat/completions format."""

    def build_url(self) -> str:
        return f"{self.api_base}/chat/completions"

    def build_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def build_payload(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        return {k: v for k, v in payload.items() if v is not None}

    def parse_response(self, data: dict) -> LLMResponse:
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

    def parse_stream_chunk(self, line: str) -> Optional[str]:
        if line.startswith("data: "):
            line = line[6:]
        if line == "[DONE]":
            return None
        try:
            data = json.loads(line)
            delta = data.get("choices", [{}])[0].get("delta", {})
            return delta.get("content", "")
        except (json.JSONDecodeError, IndexError, KeyError):
            return None


class AnthropicProvider(BaseProvider):
    """Anthropic Claude Messages API."""
    ANTHROPIC_VERSION = "2023-06-01"

    def build_url(self) -> str:
        return f"{self.api_base}/messages"

    def build_headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

    def build_payload(self, messages: list[dict]) -> dict:
        system = None
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})
        payload = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if system:
            payload["system"] = system
        return payload

    def parse_response(self, data: dict) -> LLMResponse:
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block["text"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
        )

    def parse_stream_chunk(self, line: str) -> Optional[str]:
        if line.startswith("data: "):
            line = line[6:]
        try:
            data = json.loads(line)
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                if delta.get("type") == "text_delta":
                    return delta.get("text", "")
        except (json.JSONDecodeError, KeyError):
            pass
        return None


class AzureProvider(BaseProvider):
    """Azure OpenAI service."""
    API_VERSION = "2024-08-01-preview"

    def build_url(self) -> str:
        return f"{self.api_base}/openai/deployments/{self.model}/chat/completions?api-version={self.API_VERSION}"

    def build_headers(self) -> dict:
        return {"api-key": self.api_key, "Content-Type": "application/json"}

    def build_payload(self, messages: list[dict]) -> dict:
        payload = {"messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens}
        return {k: v for k, v in payload.items() if v is not None}

    def parse_response(self, data: dict) -> LLMResponse:
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(content=content, prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0))

    def parse_stream_chunk(self, line: str) -> Optional[str]:
        if line.startswith("data: "):
            line = line[6:]
        if line == "[DONE]":
            return None
        try:
            data = json.loads(line)
            delta = data.get("choices", [{}])[0].get("delta", {})
            return delta.get("content", "")
        except (json.JSONDecodeError, IndexError, KeyError):
            return None


class OllamaProvider(BaseProvider):
    """Ollama local API (/api/chat)."""

    def build_url(self) -> str:
        return f"{self.api_base}/api/chat"

    def build_headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def build_payload(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if self.max_tokens:
            payload["options"]["num_predict"] = self.max_tokens
        return payload

    def parse_response(self, data: dict) -> LLMResponse:
        content = data.get("message", {}).get("content", "")
        return LLMResponse(content=content, prompt_tokens=data.get("prompt_eval_count", 0), completion_tokens=data.get("eval_count", 0))

    def parse_stream_chunk(self, line: str) -> Optional[str]:
        """Ollama streaming: each line is a JSON object with message.content."""
        try:
            data = json.loads(line)
            if data.get("done", False):
                return None
            message = data.get("message", {})
            return message.get("content", "")
        except (json.JSONDecodeError, KeyError):
            return None


class GoogleProvider(BaseProvider):
    """Google Gemini API."""

    def build_url(self) -> str:
        return f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}"

    def build_headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def build_payload(self, messages: list[dict]) -> dict:
        contents = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = {"parts": [{"text": m["content"]}]}
            elif m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": self.temperature, "maxOutputTokens": self.max_tokens},
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        return payload

    def parse_response(self, data: dict) -> LLMResponse:
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            content = ""
        usage = data.get("usageMetadata", {})
        return LLMResponse(content=content, prompt_tokens=usage.get("promptTokenCount", 0), completion_tokens=usage.get("candidatesTokenCount", 0))

    def parse_stream_chunk(self, line: str) -> Optional[str]:
        """Gemini streaming: each line is JSON with candidates[0].content.parts[0].text."""
        if line.startswith("data: "):
            line = line[6:]
        try:
            data = json.loads(line)
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return None


PROVIDER_DEFAULTS = {
    "openai":      {"api_base": "https://api.openai.com/v1"},
    "anthropic":   {"api_base": "https://api.anthropic.com/v1"},
    "azure":       {"api_base": ""},
    "ollama":      {"api_base": "http://localhost:11434"},
    "google":      {"api_base": "https://generativelanguage.googleapis.com/v1beta"},
    "deepseek":    {"api_base": "https://api.deepseek.com/v1"},
    "groq":        {"api_base": "https://api.groq.com/openai/v1"},
    "together":    {"api_base": "https://api.together.xyz/v1"},
    "mistral":     {"api_base": "https://api.mistral.ai/v1"},
    "openrouter":  {"api_base": "https://openrouter.ai/api/v1"},
    "github":      {"api_base": "https://models.inference.ai.azure.com"},
    "other":       {"api_base": ""},
}


def _resolve_api_base(provider: str, api_base: Optional[str]) -> str:
    if api_base:
        return api_base
    clean = provider.strip().lower().lstrip("\ufeff")
    defaults = PROVIDER_DEFAULTS.get(clean, {})
    return defaults.get("api_base", "")


def _get_provider_class(provider: str) -> type[BaseProvider]:
    clean = provider.strip().lower().lstrip("\ufeff")
    mapping = {
        "openai": OpenAIProvider, "deepseek": OpenAIProvider, "groq": OpenAIProvider,
        "together": OpenAIProvider, "mistral": OpenAIProvider, "openrouter": OpenAIProvider,
        "github": OpenAIProvider, "other": OpenAIProvider,
        "anthropic": AnthropicProvider, "azure": AzureProvider,
        "ollama": OllamaProvider, "google": GoogleProvider,
    }
    return mapping.get(clean, OpenAIProvider)


class LLMClient:
    """Factory that creates the correct provider adapter."""

    def __init__(self, provider: str = "openai", api_base: Optional[str] = None,
                 api_key: str = "", model_name: str = "", temperature: float = 0.7, max_tokens: int = 4096):
        resolved_base = _resolve_api_base(provider, api_base)
        provider_cls = _get_provider_class(provider)
        self._adapter = provider_cls(api_base=resolved_base, api_key=api_key,
                                     model=model_name, temperature=temperature, max_tokens=max_tokens)

    async def chat_completion(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        response = await self._adapter.chat_completion(messages)
        return response.to_dict()

    async def chat_completion_raw(self, messages: list[dict[str, str]]) -> LLMResponse:
        return await self._adapter.chat_completion(messages)

    async def chat_stream(self, messages: list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream text chunks from the LLM."""
        async for chunk in self._adapter.chat_stream(messages):
            yield chunk
