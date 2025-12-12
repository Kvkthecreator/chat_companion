"""Provider-agnostic Image Generation service.

Supports multiple image generation providers through a unified interface.
Provider and model are specified at runtime, not via environment variables.

Supported providers:
- gemini: Google Gemini/Imagen - DEFAULT (uses GOOGLE_API_KEY)
- replicate: Replicate API - FLUX, Stable Diffusion, etc. (uses REPLICATE_API_TOKEN)

Environment variables (credentials only):
- GOOGLE_API_KEY: Google AI API key
- REPLICATE_API_TOKEN: Replicate API token

Usage:
    # Get a client for a specific provider/model
    client = ImageService.get_client("gemini", "imagen-3.0-generate-002")
    response = await client.generate("A cozy coffee shop")

    # Use the default instance
    service = ImageService.get_instance()
    response = await service.generate("A cozy coffee shop")
"""

import base64
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    GEMINI = "gemini"
    REPLICATE = "replicate"


@dataclass
class ImageResponse:
    """Response from image generation."""

    images: List[bytes]  # Raw image bytes
    model: str
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ImageConfig:
    """Configuration for image service."""

    provider: ImageProvider
    model: str
    api_key: Optional[str] = None
    timeout: float = 120.0


class BaseImageClient(ABC):
    """Base class for image generation clients."""

    def __init__(self, config: ImageConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def close(self):
        await self.client.aclose()

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> ImageResponse:
        """Generate images from a prompt."""
        pass


class GeminiImageClient(BaseImageClient):
    """Google Gemini (Imagen) image generation client."""

    def __init__(self, config: ImageConfig):
        super().__init__(config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = config.api_key
        self.headers = {
            "x-goog-api-key": config.api_key,
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> ImageResponse:
        start_time = time.time()

        # Determine aspect ratio from dimensions
        aspect_ratio = "1:1"
        if width > height:
            aspect_ratio = "16:9" if width / height > 1.5 else "4:3"
        elif height > width:
            aspect_ratio = "9:16" if height / width > 1.5 else "3:4"

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": num_images,
                "aspectRatio": aspect_ratio,
            },
        }

        if negative_prompt:
            payload["parameters"]["negativePrompt"] = negative_prompt

        # Use Imagen model for image generation
        model = self.config.model
        url = f"{self.base_url}/models/{model}:predict"

        response = await self.client.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract images from response
        images = []
        predictions = data.get("predictions", [])
        for pred in predictions:
            if "bytesBase64Encoded" in pred:
                image_bytes = base64.b64decode(pred["bytesBase64Encoded"])
                images.append(image_bytes)

        return ImageResponse(
            images=images,
            model=model,
            latency_ms=latency_ms,
            raw_response=data,
        )


class GeminiFlashImageClient(BaseImageClient):
    """Google Gemini Flash native image generation client.

    Uses Gemini's native multimodal capability for image generation.
    """

    def __init__(self, config: ImageConfig):
        super().__init__(config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = config.api_key

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> ImageResponse:
        start_time = time.time()

        # For Gemini Flash native image gen, we use generateContent with responseModalities
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nAvoid: {negative_prompt}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
            },
        }

        model = self.config.model
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract images from response
        images = []
        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    if inline_data.get("mimeType", "").startswith("image/"):
                        image_bytes = base64.b64decode(inline_data["data"])
                        images.append(image_bytes)

        return ImageResponse(
            images=images,
            model=model,
            latency_ms=latency_ms,
            raw_response=data,
        )


class ReplicateClient(BaseImageClient):
    """Replicate API client for image generation."""

    def __init__(self, config: ImageConfig):
        super().__init__(config)
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> ImageResponse:
        start_time = time.time()

        # Model-specific input formatting
        model = self.config.model

        # Common FLUX models
        if "flux" in model.lower():
            input_data = {
                "prompt": prompt,
                "num_outputs": num_images,
                "aspect_ratio": self._get_aspect_ratio(width, height),
                "output_format": "png",
            }
            if negative_prompt:
                input_data["negative_prompt"] = negative_prompt
        else:
            # Generic SD-style input
            input_data = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_outputs": num_images,
            }
            if negative_prompt:
                input_data["negative_prompt"] = negative_prompt

        # Create prediction
        payload = {
            "version": model,
            "input": input_data,
        }

        # Start prediction
        response = await self.client.post(
            f"{self.base_url}/predictions",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        prediction = response.json()

        # Poll for completion
        prediction_id = prediction["id"]
        max_attempts = 60  # 60 seconds max

        for _ in range(max_attempts):
            response = await self.client.get(
                f"{self.base_url}/predictions/{prediction_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            prediction = response.json()

            status = prediction["status"]
            if status == "succeeded":
                break
            elif status == "failed":
                raise Exception(f"Image generation failed: {prediction.get('error')}")
            elif status in ("starting", "processing"):
                await asyncio.sleep(1)
            else:
                raise Exception(f"Unknown status: {status}")

        latency_ms = int((time.time() - start_time) * 1000)

        # Download images
        images = []
        output = prediction.get("output", [])
        if isinstance(output, str):
            output = [output]

        for url in output:
            img_response = await self.client.get(url)
            img_response.raise_for_status()
            images.append(img_response.content)

        return ImageResponse(
            images=images,
            model=model,
            latency_ms=latency_ms,
            raw_response=prediction,
        )

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """Convert dimensions to FLUX aspect ratio string."""
        ratio = width / height
        if ratio > 1.7:
            return "16:9"
        elif ratio > 1.2:
            return "4:3"
        elif ratio < 0.6:
            return "9:16"
        elif ratio < 0.8:
            return "3:4"
        else:
            return "1:1"


# Need asyncio for Replicate polling
import asyncio


class ImageService:
    """Provider-agnostic image generation service.

    Supports two modes:
    1. Runtime configuration: get_client(provider, model) for specific needs
    2. Default instance: get_instance() for app-wide default
    """

    # Default provider/model for the app
    DEFAULT_PROVIDER = "gemini"
    DEFAULT_MODEL = "gemini-2.0-flash-exp-image-generation"

    # API key environment variable mapping
    API_KEY_ENV_VARS = {
        ImageProvider.GEMINI: "GOOGLE_API_KEY",
        ImageProvider.REPLICATE: "REPLICATE_API_TOKEN",
    }

    _instance: Optional["ImageService"] = None
    _clients: Dict[str, "ImageService"] = {}  # Cache of provider+model -> client

    def __init__(self, provider: str = None, model: str = None):
        """Initialize with specific provider/model or use defaults."""
        provider = provider or self.DEFAULT_PROVIDER
        model = model or self.DEFAULT_MODEL
        self.config = self._build_config(provider, model)
        self._client = self._create_client(self.config)

    @classmethod
    def get_instance(cls) -> "ImageService":
        """Get singleton instance with default provider/model."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_client(cls, provider: str, model: str) -> "ImageService":
        """Get a client for a specific provider/model combination.

        Clients are cached by provider+model for reuse.
        """
        cache_key = f"{provider}:{model}"
        if cache_key not in cls._clients:
            cls._clients[cache_key] = cls(provider=provider, model=model)
        return cls._clients[cache_key]

    @classmethod
    def _build_config(cls, provider: str, model: str) -> ImageConfig:
        """Build configuration for a provider/model combination."""
        try:
            provider_enum = ImageProvider(provider.lower())
        except ValueError:
            raise ValueError(f"Unknown image provider: {provider}. Supported: {[p.value for p in ImageProvider]}")

        # Get API key from environment
        api_key_var = cls.API_KEY_ENV_VARS.get(provider_enum)
        api_key = os.getenv(api_key_var) if api_key_var else None

        if api_key_var and not api_key:
            log.warning(f"No API key found for {provider} (expected {api_key_var})")

        return ImageConfig(
            provider=provider_enum,
            model=model,
            api_key=api_key,
            timeout=120.0,
        )

    @classmethod
    def _create_client(cls, config: ImageConfig) -> BaseImageClient:
        """Create the appropriate client for the configuration."""
        if config.provider == ImageProvider.GEMINI:
            # Use native Gemini image gen for flash models
            if "flash" in config.model.lower():
                return GeminiFlashImageClient(config)
            else:
                return GeminiImageClient(config)
        elif config.provider == ImageProvider.REPLICATE:
            return ReplicateClient(config)
        else:
            raise ValueError(f"No client implementation for provider: {config.provider}")

    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> ImageResponse:
        """Generate images from a prompt."""
        return await self._client.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_images=num_images,
        )

    async def close(self):
        """Close the client."""
        if self._client:
            await self._client.close()

    @property
    def provider(self) -> ImageProvider:
        return self.config.provider

    @property
    def model(self) -> str:
        return self.config.model
