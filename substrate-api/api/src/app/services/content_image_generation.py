"""Content Image Generation Service.

Generates images for Series covers and Episode backgrounds.

CANONICAL REFERENCE: docs/IMAGE_STRATEGY.md

Key Design Principles:
1. SEPARATION OF CONCERNS - Character styling vs environment rendering
2. PURPOSE-SPECIFIC PROMPTS - Each image type gets only relevant elements
3. PROMPT PRIORITY ORDER - Subject first, then context, then style
4. NO NARRATIVE CONCEPTS - Visual instructions only, not abstract mood words
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.image import ImageService

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

class ImageType:
    """Image type constants."""
    SERIES_COVER = "series_cover"
    EPISODE_BACKGROUND = "episode_background"
    CHARACTER_AVATAR = "character_avatar"
    SCENE_CARD = "scene_card"


# Aspect ratios for different image types
ASPECT_RATIOS = {
    ImageType.SERIES_COVER: (1024, 576),      # 16:9 landscape
    ImageType.EPISODE_BACKGROUND: (576, 1024), # 9:16 portrait (mobile chat)
    ImageType.CHARACTER_AVATAR: (1024, 1024),  # 1:1 square
    ImageType.SCENE_CARD: (1024, 576),         # 16:9 cinematic
}


# =============================================================================
# Episode Background Configuration
# Per-episode configs with EXPLICIT location, time, and rendering.
# ANIME STYLE: Soft romantic anime, Korean webtoon influenced
# =============================================================================

# Anime style constants for K-World
KWORLD_ANIME_STYLE = "anime illustration, soft romantic style, Korean webtoon, detailed background art"
KWORLD_ANIME_QUALITY = "masterpiece, best quality, highly detailed anime"
KWORLD_ANIME_NEGATIVE = "photorealistic, 3D render, western cartoon, harsh shadows, dark, horror, blurry, low quality"

STOLEN_MOMENTS_BACKGROUNDS = {
    "3AM": {
        "location": "anime convenience store interior, fluorescent lights casting soft glow, colorful snack packages on shelves, glass doors showing rainy night outside",
        "time": "late night 3am atmosphere, warm fluorescent glow, gentle light reflections",
        "mood": "quiet lonely beauty, romantic solitude, chance encounter feeling",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Rooftop Rain": {
        "location": "anime rooftop scene, Seoul city skyline with glowing lights below, puddles reflecting city colors, low wall ledge",
        "time": "dusk turning to evening, soft rain falling, dreamy city lights emerging",
        "mood": "romantic melancholy, anticipation, beautiful sadness",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Old Songs": {
        "location": "cozy anime apartment living room, warm lamp light, acoustic guitar against wall, vinyl records scattered, soft cushions",
        "time": "late night, warm golden lamp glow, intimate darkness outside windows",
        "mood": "intimate warmth, vulnerability, creative space",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Seen": {
        "location": "anime back alley scene, wet pavement with neon reflections, soft bokeh lights in distance, narrow atmospheric passage",
        "time": "night, colorful neon glow mixing with shadows, rain-slicked surfaces",
        "mood": "hidden moment, exciting tension, stolen privacy",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Morning After": {
        "location": "soft anime bedroom, white rumpled bedding, sheer curtains with light filtering through, minimal cozy decor, plants by window",
        "time": "early morning, soft golden sunlight through curtains, gentle warm glow",
        "mood": "tender intimacy, quiet vulnerability, new beginnings",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "One More Night": {
        "location": "anime luxury hotel room, large window showing sparkling city night view, modern elegant furnishings, soft ambient lighting",
        "time": "evening, city lights twinkling through window, warm interior glow",
        "mood": "romantic anticipation, elegant desire, bittersweet longing",
        "rendering": KWORLD_ANIME_STYLE,
    },
}

# Weekend Regular series backgrounds
WEEKEND_REGULAR_BACKGROUNDS = {
    "Extra Shot": {
        "location": "cozy anime café interior, warm wood tones, large windows with afternoon sunlight streaming in, coffee bar visible in background, plants and books on shelves, comfortable seating",
        "time": "afternoon, warm golden sunlight, soft shadows, peaceful Sunday atmosphere",
        "mood": "comfortable warmth, gentle anticipation, familiar space becoming significant",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Last Call": {
        "location": "anime café at closing time, chairs stacked on some tables, warm pendant lights dimmed low, rain visible through windows, empty intimate space, cleaning supplies nearby",
        "time": "evening closing time, soft warm interior lights against rain outside, quiet solitude",
        "mood": "intimate possibility, gentle tension, the magic of empty spaces after hours",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Page 47": {
        "location": "cozy anime café corner booth, wooden table with open sketchbook, coffee cups, afternoon light catching dust particles, intimate seating arrangement",
        "time": "afternoon, soft diffused light through windows, warm and quiet atmosphere",
        "mood": "vulnerability, trust, artistic intimacy, shared secrets between two people",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Different Context": {
        "location": "anime evening street scene, quiet neighborhood, soft streetlights beginning to glow, small shops with warm lights, residential area feel",
        "time": "early evening, golden hour fading to blue hour, warm streetlights emerging",
        "mood": "chance encounter magic, new possibilities, outside the usual context",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Your Usual": {
        "location": "small anime apartment kitchen, morning light through window, pour-over coffee setup on counter, art supplies and sketches visible, cozy creative living space",
        "time": "morning, soft golden sunlight filtering in, peaceful domestic atmosphere",
        "mood": "morning after tenderness, domestic intimacy, new chapter beginning",
        "rendering": KWORLD_ANIME_STYLE,
    },
    "Reserved": {
        "location": "anime café interior, familiar wooden table by window, hand-drawn reserved sign on table, two coffee cups, warm welcoming atmosphere",
        "time": "afternoon, warm familiar lighting, comfortable and meaningful sunlight",
        "mood": "full circle, belonging, quiet declaration of something special",
        "rendering": KWORLD_ANIME_STYLE,
    },
}

# Combined lookup for all series
ALL_EPISODE_BACKGROUNDS = {
    **STOLEN_MOMENTS_BACKGROUNDS,
    **WEEKEND_REGULAR_BACKGROUNDS,
}


# =============================================================================
# Negative Prompts (Purpose-Specific)
# =============================================================================

BACKGROUND_NEGATIVE = """people, person, character, figure, silhouette, face, portrait, human,
photorealistic, 3D render, western cartoon, CGI,
text, watermark, signature, logo,
blurry, low quality, distorted, dark, gritty, horror"""

SERIES_COVER_NEGATIVE = """multiple people, crowd, group,
photorealistic, 3D render, western cartoon, chibi,
text, watermark, signature, logo,
blurry, low quality, distorted, bad anatomy, extra limbs, dark, horror"""

CHARACTER_NEGATIVE = """multiple people, crowd,
blurry face, distorted face, extra limbs, bad anatomy,
text, watermark, signature,
low quality, worst quality"""


# =============================================================================
# Prompt Builders - Episode Background
# =============================================================================

def build_episode_background_prompt(
    episode_title: str,
    episode_config: Optional[Dict[str, str]] = None,
    fallback_situation: Optional[str] = None,
) -> tuple[str, str]:
    """
    Build prompt for episode background image.

    CANONICAL STRUCTURE (docs/IMAGE_STRATEGY.md):
    1. Style declaration (anime first for model to understand)
    2. Location description
    3. Time of day / lighting
    4. Mood / atmosphere
    5. Quality markers
    6. Constraints (no people)

    Args:
        episode_title: Episode title for config lookup
        episode_config: Optional explicit config dict with location/time/mood/rendering
        fallback_situation: Fallback situation text if no config found

    Returns:
        Tuple of (positive_prompt, negative_prompt)
    """
    # Get episode-specific config (check all series backgrounds)
    config = episode_config or ALL_EPISODE_BACKGROUNDS.get(episode_title, {})

    if config:
        location = config.get("location", "")
        time = config.get("time", "")
        mood = config.get("mood", "")
        rendering = config.get("rendering", KWORLD_ANIME_STYLE)
    elif fallback_situation:
        # Extract what we can from situation text (less ideal)
        location = f"anime scene, {fallback_situation[:120]}"
        time = ""
        mood = "atmospheric, emotional"
        rendering = KWORLD_ANIME_STYLE
    else:
        raise ValueError(f"No config found for episode '{episode_title}' and no fallback provided")

    # Build prompt with STYLE FIRST (helps model understand the aesthetic)
    prompt_parts = [
        rendering,                                   # 1. STYLE - anime first
        location,                                    # 2. SUBJECT - what the scene is
        time,                                        # 3. CONTEXT - when/lighting
        mood,                                        # 4. MOOD - emotional atmosphere
        "atmospheric depth, soft lighting, beautiful composition",  # 5. COMPOSITION
        "empty scene, no people, no characters, no figures",  # 6. CONSTRAINTS
        KWORLD_ANIME_QUALITY,                        # 7. QUALITY
    ]

    # Filter empty parts and join
    prompt = ", ".join(p for p in prompt_parts if p)

    return prompt, BACKGROUND_NEGATIVE


# =============================================================================
# Prompt Builders - Series Cover
# =============================================================================

def build_series_cover_prompt(
    character_description: str,
    scene_description: str,
    pose_and_expression: str,
    lighting_and_time: str,
    genre_style: str = "cinematic",
) -> tuple[str, str]:
    """
    Build prompt for series cover image (character IN scene).

    CANONICAL STRUCTURE (docs/IMAGE_STRATEGY.md):
    1. Character description (WHO)
    2. Pose and position in scene (WHAT they're doing)
    3. Scene/environment description (WHERE)
    4. Lighting and time of day
    5. Composition and style
    6. Quality markers

    Args:
        character_description: Full character appearance
        scene_description: Environmental context
        pose_and_expression: What the character is doing/feeling
        lighting_and_time: Time of day and lighting setup
        genre_style: Genre-appropriate style cues

    Returns:
        Tuple of (positive_prompt, negative_prompt)
    """
    prompt_parts = [
        character_description,                       # 1. WHO
        pose_and_expression,                         # 2. WHAT
        f"in {scene_description}",                   # 3. WHERE
        lighting_and_time,                           # 4. LIGHTING
        f"cinematic wide shot, {genre_style}",       # 5. COMPOSITION
        "atmospheric depth, highly detailed",        # 6. DETAIL
        "masterpiece, best quality",                 # 7. QUALITY
    ]

    prompt = ", ".join(p for p in prompt_parts if p)

    return prompt, SERIES_COVER_NEGATIVE


def build_stolen_moments_cover_prompt() -> tuple[str, str]:
    """
    Build the specific series cover prompt for Stolen Moments.

    Returns anime-style character-in-scene prompt for Soo-ah.
    """
    return build_series_cover_prompt(
        character_description="beautiful anime girl, young Korean woman in her mid-20s, soft features, expressive tired eyes, hair in simple ponytail, wearing oversized hoodie with mask pulled down, vulnerable beauty",
        scene_description="anime Seoul street at night, soft neon glow reflecting on rain-wet pavement, dreamy urban atmosphere, bokeh city lights",
        pose_and_expression="standing alone, looking back over shoulder with guarded but curious expression, slight blush, emotional eyes",
        lighting_and_time="night scene, soft colorful neon reflections, warm and cool tones mixing, gentle atmospheric glow",
        genre_style="romantic anime style, Korean webtoon aesthetic, soft cel-shading, emotional atmosphere",
    )


def build_weekend_regular_cover_prompt() -> tuple[str, str]:
    """
    Build the specific series cover prompt for Weekend Regular.

    Returns anime-style character-in-scene prompt for Minji the barista.
    """
    return build_series_cover_prompt(
        character_description="beautiful anime girl, young Korean woman early 20s, soft gentle features, warm brown eyes, hair in low ponytail with loose strands framing face, wearing café apron over casual sweater, paint-stained fingers, gentle warm smile",
        scene_description="cozy anime café interior, warm afternoon sunlight through large windows, wooden counter and coffee equipment, plants and books in background, inviting atmosphere",
        pose_and_expression="leaning slightly on counter, holding coffee cup, looking at viewer with shy but warm expression, slight blush, eyes that have been watching",
        lighting_and_time="afternoon golden hour, warm sunlight streaming through windows, soft cozy atmosphere",
        genre_style="romantic anime style, slice of life aesthetic, soft warm colors, Korean webtoon influence, gentle everyday magic",
    )


# Series cover prompt lookup
SERIES_COVER_PROMPTS = {
    "stolen-moments": build_stolen_moments_cover_prompt,
    "weekend-regular": build_weekend_regular_cover_prompt,
}


# =============================================================================
# Main Generation Service
# =============================================================================

class ContentImageGenerator:
    """
    Generates content images (series covers, episode backgrounds).

    Uses purpose-specific prompt building - no cascade confusion.
    """

    def __init__(self, provider: str = "replicate", model: str = "black-forest-labs/flux-1.1-pro"):
        """Initialize with specified provider/model."""
        self.provider = provider
        self.model = model

    def _get_service(self) -> ImageService:
        """Get image service client."""
        return ImageService.get_client(self.provider, self.model)

    async def generate_episode_background(
        self,
        episode_title: str,
        episode_config: Optional[Dict[str, str]] = None,
        fallback_situation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an episode background image.

        Args:
            episode_title: Episode title (e.g., "3AM")
            episode_config: Optional explicit config dict
            fallback_situation: Fallback text if no config

        Returns:
            Dict with image bytes, prompt, model info
        """
        prompt, negative = build_episode_background_prompt(
            episode_title=episode_title,
            episode_config=episode_config,
            fallback_situation=fallback_situation,
        )

        width, height = ASPECT_RATIOS[ImageType.EPISODE_BACKGROUND]

        log.info(f"Generating episode background for '{episode_title}'")
        log.info(f"Prompt: {prompt[:200]}...")

        service = self._get_service()
        result = await service.generate(
            prompt=prompt,
            negative_prompt=negative,
            width=width,
            height=height,
        )

        return {
            "images": result.images,
            "prompt": prompt,
            "negative_prompt": negative,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "image_type": ImageType.EPISODE_BACKGROUND,
        }

    async def generate_series_cover(
        self,
        character_description: str,
        scene_description: str,
        pose_and_expression: str,
        lighting_and_time: str,
        genre_style: str = "cinematic",
        use_reference: bool = False,
        reference_image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Generate a series cover image (character in scene).

        Args:
            character_description: Full character appearance
            scene_description: Environmental context
            pose_and_expression: Character action/emotion
            lighting_and_time: Lighting setup
            genre_style: Genre-specific style cues
            use_reference: Whether to use FLUX Kontext with reference
            reference_image_bytes: Character anchor image if using reference

        Returns:
            Dict with image bytes, prompt, model info
        """
        prompt, negative = build_series_cover_prompt(
            character_description=character_description,
            scene_description=scene_description,
            pose_and_expression=pose_and_expression,
            lighting_and_time=lighting_and_time,
            genre_style=genre_style,
        )

        width, height = ASPECT_RATIOS[ImageType.SERIES_COVER]

        log.info(f"Generating series cover")
        log.info(f"Prompt: {prompt[:200]}...")

        if use_reference and reference_image_bytes:
            # Use FLUX Kontext for character consistency
            service = ImageService.get_client("replicate", "black-forest-labs/flux-kontext-pro")
            # Modify prompt to reference the input image
            kontext_prompt = f"Same person from reference image, {pose_and_expression}, in {scene_description}, {lighting_and_time}, cinematic wide shot, {genre_style}, masterpiece"
            result = await service.edit(
                prompt=kontext_prompt,
                reference_images=[reference_image_bytes],
                aspect_ratio="16:9",
            )
            prompt = kontext_prompt  # Update for return
        else:
            # Standard text-to-image
            service = self._get_service()
            result = await service.generate(
                prompt=prompt,
                negative_prompt=negative,
                width=width,
                height=height,
            )

        return {
            "images": result.images,
            "prompt": prompt,
            "negative_prompt": negative,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "image_type": ImageType.SERIES_COVER,
            "used_reference": use_reference,
        }

    async def generate_stolen_moments_cover(
        self,
        use_reference: bool = False,
        reference_image_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Generate the Stolen Moments series cover specifically.

        Convenience method with pre-configured prompt for Soo-ah.
        """
        return await self.generate_series_cover(
            character_description="Young Korean woman in her mid-20s, natural beauty, tired but striking eyes, hair pulled back simply, wearing oversized hoodie with mask pulled down around chin",
            scene_description="empty neon-lit Seoul street at night, rain-wet pavement reflecting colorful signs, urban isolation",
            pose_and_expression="standing alone, looking back over shoulder with guarded but curious expression, slight tension in posture",
            lighting_and_time="night, neon lights reflecting on wet street, mix of warm and cool tones",
            genre_style="K-drama romantic tension aesthetic, moody urban atmosphere",
            use_reference=use_reference,
            reference_image_bytes=reference_image_bytes,
        )


# =============================================================================
# Batch Generation Helpers
# =============================================================================

async def generate_all_episode_backgrounds(
    series_slug: str,
    episode_configs: Dict[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    """
    Generate backgrounds for all episodes in a series.

    Args:
        series_slug: Series identifier
        episode_configs: Dict mapping episode titles to their configs

    Returns:
        List of generation results
    """
    generator = ContentImageGenerator()
    results = []

    for title, config in episode_configs.items():
        try:
            result = await generator.generate_episode_background(
                episode_title=title,
                episode_config=config,
            )
            result["episode_title"] = title
            result["success"] = True
            results.append(result)
            log.info(f"Generated background for '{title}'")
        except Exception as e:
            log.error(f"Failed to generate background for '{title}': {e}")
            results.append({
                "episode_title": title,
                "success": False,
                "error": str(e),
            })

    return results
