"""Content Image Generation Service.

Generates images for Series covers and Episode backgrounds using
the Visual Identity Cascade system:

World visual_style → Series visual_style → Episode-specific context

Reference: docs/IMAGE_STRATEGY.md
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.image import ImageService

log = logging.getLogger(__name__)


# =============================================================================
# Fantazy Style Lock - Applied to ALL generated images
# =============================================================================

FANTAZY_STYLE_LOCK = """masterpiece, best quality, highly detailed illustration,
cinematic lighting, soft dramatic shadows, professional quality,
cohesive color palette, atmospheric depth"""

FANTAZY_NEGATIVE_LOCK = """lowres, bad anatomy, bad hands, text, error,
missing fingers, extra digit, fewer digits, cropped, worst quality,
low quality, normal quality, jpeg artifacts, signature, watermark,
username, blurry, deformed, disfigured, mutation, mutated"""


# =============================================================================
# Image Type Templates
# =============================================================================

class ImageType:
    """Image type constants."""
    SERIES_COVER = "series_cover"
    EPISODE_BACKGROUND = "episode_background"
    WORLD_HERO = "world_hero"


# Aspect ratios for different image types
ASPECT_RATIOS = {
    ImageType.SERIES_COVER: (1024, 576),  # 16:9 landscape
    ImageType.EPISODE_BACKGROUND: (576, 1024),  # 9:16 portrait (for mobile chat)
    ImageType.WORLD_HERO: (1024, 576),  # 16:9 landscape
}


# =============================================================================
# Visual Style Cascade
# =============================================================================

def merge_visual_styles(
    world_style: Dict[str, Any],
    series_style: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge world and series visual styles with cascade inheritance.

    Series-level values override world-level values where specified.
    """
    merged = dict(world_style)  # Start with world as base

    if series_style:
        for key, value in series_style.items():
            if value is not None and value != "":
                # Series overrides world for non-empty values
                if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                    # For lists (like recurring_motifs), extend rather than replace
                    merged[key] = merged[key] + value
                else:
                    merged[key] = value

    return merged


def build_style_prompt(visual_style: Dict[str, Any]) -> str:
    """
    Build a style prompt string from visual_style dict.

    Returns a coherent prompt fragment for image generation.
    """
    parts = []

    if visual_style.get("base_style"):
        parts.append(visual_style["base_style"])

    if visual_style.get("color_palette"):
        parts.append(visual_style["color_palette"])

    if visual_style.get("rendering"):
        parts.append(visual_style["rendering"])

    if visual_style.get("atmosphere"):
        parts.append(visual_style["atmosphere"])

    if visual_style.get("mood"):
        parts.append(f"{visual_style['mood']} mood")

    if visual_style.get("genre_markers"):
        parts.append(visual_style["genre_markers"])

    return ", ".join(parts)


def build_negative_prompt(visual_style: Dict[str, Any]) -> str:
    """
    Build negative prompt from visual_style + Fantazy defaults.
    """
    parts = [FANTAZY_NEGATIVE_LOCK]

    if visual_style.get("negative_prompt"):
        parts.append(visual_style["negative_prompt"])

    return ", ".join(parts)


# =============================================================================
# Prompt Builders
# =============================================================================

def build_series_cover_prompt(
    series_title: str,
    series_tagline: Optional[str],
    series_genre: Optional[str],
    visual_style: Dict[str, Any],
    world_name: Optional[str] = None,
) -> str:
    """
    Build prompt for series cover image.

    Focus: Atmospheric, mood-focused, setting-centric (NO characters)
    """
    style_prompt = build_style_prompt(visual_style)

    # Extract motifs if available
    motifs = visual_style.get("recurring_motifs", [])
    motif_str = ", ".join(motifs[:3]) if motifs else ""

    # Build the core prompt
    prompt_parts = [
        f"cinematic establishing shot",
        f"atmospheric scene representing '{series_title}'",
    ]

    if series_tagline:
        prompt_parts.append(f"evoking the feeling of '{series_tagline}'")

    if series_genre:
        prompt_parts.append(f"{series_genre} genre aesthetic")

    if motif_str:
        prompt_parts.append(f"featuring {motif_str}")

    # Add style
    prompt_parts.append(style_prompt)
    prompt_parts.append(FANTAZY_STYLE_LOCK)

    # Critical: NO characters
    prompt_parts.append("empty scene, no people, no characters, no faces")

    return ", ".join(prompt_parts)


def build_episode_background_prompt(
    episode_title: str,
    episode_situation: str,
    visual_style: Dict[str, Any],
    time_of_day: Optional[str] = None,
    location_hint: Optional[str] = None,
) -> str:
    """
    Build prompt for episode background image.

    Focus: Empty environment, atmospheric, suitable as chat backdrop
    """
    style_prompt = build_style_prompt(visual_style)

    prompt_parts = [
        "atmospheric background scene",
        "empty environment",
    ]

    # Extract location from situation if not provided
    if location_hint:
        prompt_parts.append(f"{location_hint} setting")
    elif episode_situation:
        # Try to extract location context from situation
        prompt_parts.append(f"scene setting for: {episode_situation[:100]}")

    if time_of_day:
        prompt_parts.append(f"{time_of_day} lighting")

    # Add style
    prompt_parts.append(style_prompt)
    prompt_parts.append(FANTAZY_STYLE_LOCK)

    # Critical for backgrounds
    prompt_parts.extend([
        "soft atmospheric blur",
        "suitable for text overlay",
        "no people",
        "no characters",
        "no faces",
        "empty scene",
    ])

    return ", ".join(prompt_parts)


# =============================================================================
# Episode Background Concepts
# =============================================================================

# Pre-defined location/time concepts for common episode situations
EPISODE_LOCATION_CONCEPTS = {
    # K-World typical locations
    "convenience_store": "fluorescent-lit Korean convenience store interior, konbini, late night quiet, snack aisles",
    "cafe": "cozy Korean café interior, warm lighting, rain outside window, coffee shop ambiance",
    "subway": "empty Seoul subway platform, last train atmosphere, urban transit",
    "rooftop": "Seoul rooftop at dusk, city lights below, golden hour fading to night",
    "apartment_hallway": "dim apartment building corridor, soft light under doors, residential",
    "bar": "intimate Korean bar interior, closing time, neon signs dimming, soju bottles",
    "park": "Seoul park at twilight, autumn leaves, park bench, city skyline distant",
    "office": "late night office, desk lamp lighting, city view through window",
    "street": "rainy Seoul street at night, neon reflections on wet pavement",
    "beach": "Korean beach at sunset, waves, distant pier, romantic atmosphere",
}


def get_location_concept(location_key: str) -> Optional[str]:
    """Get pre-defined location concept by key."""
    return EPISODE_LOCATION_CONCEPTS.get(location_key.lower().replace(" ", "_"))


# =============================================================================
# Main Generation Service
# =============================================================================

class ContentImageGenerator:
    """
    Generates content images (series covers, episode backgrounds)
    using the Visual Identity Cascade system.
    """

    def __init__(self):
        self.image_service = ImageService.get_instance()

    async def generate_series_cover(
        self,
        series_title: str,
        series_tagline: Optional[str],
        series_genre: Optional[str],
        world_visual_style: Dict[str, Any],
        series_visual_style: Optional[Dict[str, Any]] = None,
        world_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a series cover image.

        Returns:
            Dict with 'image_url', 'prompt', 'model_used'
        """
        # Merge visual styles
        merged_style = merge_visual_styles(world_visual_style, series_visual_style)

        # Build prompt
        prompt = build_series_cover_prompt(
            series_title=series_title,
            series_tagline=series_tagline,
            series_genre=series_genre,
            visual_style=merged_style,
            world_name=world_name,
        )

        negative_prompt = build_negative_prompt(merged_style)

        # Get dimensions
        width, height = ASPECT_RATIOS[ImageType.SERIES_COVER]

        log.info(f"Generating series cover for '{series_title}'")
        log.debug(f"Prompt: {prompt}")

        # Generate
        result = await self.image_service.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
        )

        return {
            "image_url": result.image_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model_used": result.model_used,
            "latency_ms": result.latency_ms,
            "image_type": ImageType.SERIES_COVER,
        }

    async def generate_episode_background(
        self,
        episode_title: str,
        episode_situation: str,
        world_visual_style: Dict[str, Any],
        series_visual_style: Optional[Dict[str, Any]] = None,
        location_key: Optional[str] = None,
        time_of_day: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an episode background image.

        Args:
            episode_title: Episode title (e.g., "3AM")
            episode_situation: Episode situation/description
            world_visual_style: World's visual_style dict
            series_visual_style: Series' visual_style dict (optional)
            location_key: Key for pre-defined location concept
            time_of_day: Time hint (e.g., "late night", "dusk")

        Returns:
            Dict with 'image_url', 'prompt', 'model_used'
        """
        # Merge visual styles
        merged_style = merge_visual_styles(world_visual_style, series_visual_style)

        # Get location concept if key provided
        location_hint = None
        if location_key:
            location_hint = get_location_concept(location_key)

        # Build prompt
        prompt = build_episode_background_prompt(
            episode_title=episode_title,
            episode_situation=episode_situation,
            visual_style=merged_style,
            time_of_day=time_of_day,
            location_hint=location_hint,
        )

        negative_prompt = build_negative_prompt(merged_style)

        # Get dimensions (portrait for mobile chat background)
        width, height = ASPECT_RATIOS[ImageType.EPISODE_BACKGROUND]

        log.info(f"Generating episode background for '{episode_title}'")
        log.debug(f"Prompt: {prompt}")

        # Generate
        result = await self.image_service.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
        )

        return {
            "image_url": result.image_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model_used": result.model_used,
            "latency_ms": result.latency_ms,
            "image_type": ImageType.EPISODE_BACKGROUND,
        }

    async def generate_batch_episode_backgrounds(
        self,
        episodes: List[Dict[str, Any]],
        world_visual_style: Dict[str, Any],
        series_visual_style: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate backgrounds for multiple episodes.

        Args:
            episodes: List of dicts with 'title', 'situation', 'location_key', 'time_of_day'
            world_visual_style: World's visual_style dict
            series_visual_style: Series' visual_style dict

        Returns:
            List of generation results
        """
        results = []

        for ep in episodes:
            try:
                result = await self.generate_episode_background(
                    episode_title=ep.get("title", ""),
                    episode_situation=ep.get("situation", ""),
                    world_visual_style=world_visual_style,
                    series_visual_style=series_visual_style,
                    location_key=ep.get("location_key"),
                    time_of_day=ep.get("time_of_day"),
                )
                result["episode_title"] = ep.get("title")
                result["episode_id"] = ep.get("id")
                result["success"] = True
                results.append(result)
            except Exception as e:
                log.error(f"Failed to generate background for '{ep.get('title')}': {e}")
                results.append({
                    "episode_title": ep.get("title"),
                    "episode_id": ep.get("id"),
                    "success": False,
                    "error": str(e),
                })

        return results


# =============================================================================
# Convenience Functions
# =============================================================================

async def generate_series_images(
    db,
    series_id: UUID,
    generate_cover: bool = True,
    generate_backgrounds: bool = True,
) -> Dict[str, Any]:
    """
    Generate all images for a series (cover + episode backgrounds).

    Fetches series, world, and episode data from database,
    applies visual identity cascade, and generates images.
    """
    # Fetch series with world
    series_query = """
        SELECT s.*, w.visual_style as world_visual_style, w.name as world_name
        FROM series s
        LEFT JOIN worlds w ON s.world_id = w.id
        WHERE s.id = :series_id
    """
    series_row = await db.fetch_one(series_query, {"series_id": str(series_id)})

    if not series_row:
        raise ValueError(f"Series {series_id} not found")

    series_data = dict(series_row)
    world_style = series_data.get("world_visual_style") or {}
    series_style = series_data.get("visual_style") or {}

    generator = ContentImageGenerator()
    results = {"series_id": str(series_id), "cover": None, "backgrounds": []}

    # Generate cover
    if generate_cover:
        try:
            cover_result = await generator.generate_series_cover(
                series_title=series_data["title"],
                series_tagline=series_data.get("tagline"),
                series_genre=series_data.get("genre"),
                world_visual_style=world_style,
                series_visual_style=series_style,
                world_name=series_data.get("world_name"),
            )
            results["cover"] = cover_result
        except Exception as e:
            log.error(f"Failed to generate series cover: {e}")
            results["cover"] = {"success": False, "error": str(e)}

    # Generate episode backgrounds
    if generate_backgrounds:
        episodes_query = """
            SELECT id, title, situation, episode_number
            FROM episode_templates
            WHERE series_id = :series_id
            ORDER BY episode_number
        """
        episode_rows = await db.fetch_all(episodes_query, {"series_id": str(series_id)})

        episodes = [dict(row) for row in episode_rows]
        background_results = await generator.generate_batch_episode_backgrounds(
            episodes=episodes,
            world_visual_style=world_style,
            series_visual_style=series_style,
        )
        results["backgrounds"] = background_results

    return results
