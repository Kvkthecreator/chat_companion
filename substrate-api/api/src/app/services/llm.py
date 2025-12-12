"""Provider-agnostic LLM service.

Supports multiple LLM providers through a unified interface.
Provider and model are specified at runtime, not via environment variables.

Supported providers:
- google: Google Gemini API (Gemini Flash, Gemini Pro) - DEFAULT
- openai: OpenAI API (GPT-4, GPT-4o-mini)
- anthropic: Anthropic API (Claude)
- openrouter: OpenRouter (access to many models via single API)
- ollama: Local Ollama instance (self-hosted)

Environment variables (credentials only):
- GOOGLE_API_KEY: Google AI API key
- OPENAI_API_KEY: OpenAI API key
- ANTHROPIC_API_KEY: Anthropic API key
- OPENROUTER_API_KEY: OpenRouter API key

Usage:
    # Get a client for a specific provider/model
    client = LLMService.get_client("google", "gemini-2.0-flash")
    response = await client.generate(messages)

    # Use the default instance (google/gemini-2.0-flash)
    service = LLMService.get_instance()
    response = await service.generate(messages)

    # In the future: user-selected provider from their preferences
    user_provider = user.preferences.get("llm_provider", "google")
    user_model = user.preferences.get("llm_model", "gemini-2.0-flash")
    client = LLMService.get_client(user_provider, user_model)
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """Configuration for LLM service."""

    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.8
    max_tokens: int = 1024
    timeout: float = 60.0


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def close(self):
        await self.client.aclose()

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        start_time = time.time()

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.config.model),
            tokens_input=data.get("usage", {}).get("prompt_tokens"),
            tokens_output=data.get("usage", {}).get("completion_tokens"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True,
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


class AnthropicClient(BaseLLMClient):
    """Anthropic API client."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        start_time = time.time()

        # Extract system message if present
        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }
        if system_content:
            payload["system"] = system_content

        response = await self.client.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=data["content"][0]["text"],
            model=data.get("model", self.config.model),
            tokens_input=data.get("usage", {}).get("input_tokens"),
            tokens_output=data.get("usage", {}).get("output_tokens"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        # Extract system message
        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "stream": True,
        }
        if system_content:
            payload["system"] = system_content

        async with self.client.stream(
            "POST",
            f"{self.base_url}/messages",
            headers=self.headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data["type"] == "content_block_delta":
                            yield data["delta"].get("text", "")
                    except json.JSONDecodeError:
                        continue


class OpenRouterClient(OpenAIClient):
    """OpenRouter client (OpenAI-compatible)."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "https://fantazy.app"),
            "X-Title": "Fantazy",
        }


class OllamaClient(BaseLLMClient):
    """Ollama local client."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        start_time = time.time()

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=data["message"]["content"],
            model=data.get("model", self.config.model),
            tokens_input=data.get("prompt_eval_count"),
            tokens_output=data.get("eval_count"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            },
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


class GeminiClient(BaseLLMClient):
    """Google Gemini API client."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = config.api_key

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        start_time = time.time()

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature or self.config.temperature,
                "maxOutputTokens": max_tokens or self.config.max_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"{self.base_url}/models/{self.config.model}:generateContent?key={self.api_key}"

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract content from response
        content = ""
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                content = candidate["content"]["parts"][0].get("text", "")

        # Extract token counts
        usage = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=self.config.model,
            tokens_input=usage.get("promptTokenCount"),
            tokens_output=usage.get("candidatesTokenCount"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature or self.config.temperature,
                "maxOutputTokens": max_tokens or self.config.max_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"{self.base_url}/models/{self.config.model}:streamGenerateContent?alt=sse&key={self.api_key}"

        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "candidates" in data and len(data["candidates"]) > 0:
                            candidate = data["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                text = candidate["content"]["parts"][0].get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue


class LLMService:
    """Provider-agnostic LLM service.

    Supports two modes:
    1. Runtime configuration: get_client(provider, model) for specific needs
    2. Default instance: get_instance() for app-wide default (uses env vars or defaults)

    Environment variables:
    - LLM_PROVIDER: Provider name (google, openai, anthropic, etc.) - defaults to "google"
    - LLM_MODEL: Model name - defaults to "gemini-2.0-flash"
    """

    # Fallback defaults if env vars not set
    FALLBACK_PROVIDER = "google"
    FALLBACK_MODEL = "gemini-2.0-flash"

    @classmethod
    def _get_default_provider(cls) -> str:
        return os.getenv("LLM_PROVIDER", cls.FALLBACK_PROVIDER)

    @classmethod
    def _get_default_model(cls) -> str:
        return os.getenv("LLM_MODEL", cls.FALLBACK_MODEL)

    # API key environment variable mapping
    API_KEY_ENV_VARS = {
        LLMProvider.OPENAI: "OPENAI_API_KEY",
        LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        LLMProvider.GOOGLE: "GOOGLE_API_KEY",
        LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
        LLMProvider.OLLAMA: None,
    }

    # Client class mapping
    CLIENT_CLASSES = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.GOOGLE: GeminiClient,
        LLMProvider.OPENROUTER: OpenRouterClient,
        LLMProvider.OLLAMA: OllamaClient,
    }

    _instance: Optional["LLMService"] = None
    _clients: Dict[str, BaseLLMClient] = {}  # Cache of provider+model -> client

    def __init__(self, provider: str = None, model: str = None):
        """Initialize with specific provider/model or use defaults from env vars."""
        provider = provider or self._get_default_provider()
        model = model or self._get_default_model()
        self.config = self._build_config(provider, model)
        self._client = self._create_client(self.config)

    @classmethod
    def get_instance(cls) -> "LLMService":
        """Get singleton instance with default provider/model."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_client(
        cls,
        provider: str,
        model: str,
        temperature: float = 0.8,
        max_tokens: int = 1024,
    ) -> "LLMService":
        """Get a client for a specific provider/model combination.

        Clients are cached by provider+model for reuse.

        Args:
            provider: Provider name (google, openai, anthropic, etc.)
            model: Model name (gemini-2.0-flash, gpt-4o-mini, etc.)
            temperature: Default temperature for generations
            max_tokens: Default max tokens for generations

        Returns:
            LLMService instance configured for the specified provider/model
        """
        cache_key = f"{provider}:{model}"
        if cache_key not in cls._clients:
            cls._clients[cache_key] = cls(provider=provider, model=model)
        return cls._clients[cache_key]

    @classmethod
    def _build_config(cls, provider: str, model: str) -> LLMConfig:
        """Build configuration for a provider/model combination."""
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: {[p.value for p in LLMProvider]}")

        # Get API key from environment
        api_key_var = cls.API_KEY_ENV_VARS.get(provider_enum)
        api_key = os.getenv(api_key_var) if api_key_var else None

        if api_key_var and not api_key:
            log.warning(f"No API key found for {provider} (expected {api_key_var})")

        return LLMConfig(
            provider=provider_enum,
            model=model,
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL"),  # Optional override
            temperature=0.8,
            max_tokens=1024,
            timeout=60.0,
        )

    @classmethod
    def _create_client(cls, config: LLMConfig) -> BaseLLMClient:
        """Create the appropriate client for the configuration."""
        client_class = cls.CLIENT_CLASSES.get(config.provider)
        if not client_class:
            raise ValueError(f"No client implementation for provider: {config.provider}")
        return client_class(config)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        return await self._client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        async for chunk in self._client.generate_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def extract_json(
        self,
        prompt: str,
        schema_description: str,
    ) -> Dict[str, Any]:
        """Generate structured JSON output.

        Uses a system prompt to encourage JSON output.
        """
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful assistant that extracts structured information.
Always respond with valid JSON matching this schema:
{schema_description}

Respond ONLY with the JSON, no additional text.""",
            },
            {"role": "user", "content": prompt},
        ]

        response = await self.generate(messages, temperature=0.3)

        # Try to parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        return json.loads(content)

    async def close(self):
        """Close the client."""
        if self._client:
            await self._client.close()

    @property
    def provider(self) -> LLMProvider:
        return self.config.provider

    @property
    def model(self) -> str:
        return self.config.model
