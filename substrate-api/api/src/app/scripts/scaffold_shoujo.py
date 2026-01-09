"""Scaffold classic Shoujo romance series.

This script creates:
- "[Shoujo] First Snow" series
- Character: Yuki Aoyama (soft-spoken artist senpai)
- 6 episodes of classic first love romance
- All images generated with pure shoujo manga aesthetic

Style follows ADR-007: Style-first prompt architecture.
Target audience: Shoujo manga readers, first love romance seekers.

Genre considerations:
- Classic shoujo tropes: senpai/kouhai, art club, gentle tension
- Slow burn emotional development, not instant chemistry
- Soft, dreamy visuals with flower motifs and sparkles
- Emphasis on internal emotional experience
- The "doki doki" moments - racing hearts, accidental touches
- Innocent but intense - every small interaction matters

Dopamine hooks:
- Gentle tension that builds (will-they-won't-they)
- Soft validation (he notices small things about you)
- Protected feeling (he's quietly caring without being overbearing)
- Earned intimacy (each episode escalates slightly)

Usage:
    python -m app.scripts.scaffold_shoujo
    python -m app.scripts.scaffold_shoujo --dry-run
"""

import asyncio
import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://lfwhdzwbikyzalpbwfnd.supabase.co"
if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmd2hkendiaWt5emFscGJ3Zm5kIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTQzMjQ0NCwiZXhwIjoyMDgxMDA4NDQ0fQ.s2ljzY1YQkz-WTZvRa-_qzLnW1zhoL012Tn2vPOigd0"

from databases import Database
from app.services.image import ImageService
from app.services.storage import StorageService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?min_size=1&max_size=2"
)

GENERATION_DELAY = 30

# =============================================================================
# SHOUJO MANGA VISUAL STYLE DOCTRINE
# =============================================================================
# Pure shoujo aesthetic - soft, dreamy, emotionally expressive
# Key elements:
# - Soft, delicate lineart with minimal harsh shadows
# - Pastel color palette (soft pinks, lavenders, cream)
# - Flower motifs (sakura, roses) and sparkle effects
# - Large, expressive eyes with detailed highlights
# - Screentone-style shading, classic manga aesthetic
# - Backgrounds that reflect emotional state (flowers bloom during romantic moments)

SHOUJO_STYLE = "shoujo manga illustration, soft delicate lineart, classic manga aesthetic, romantic atmosphere, dreamy soft focus"
SHOUJO_QUALITY = "masterpiece, best quality, expressive eyes with sparkle highlights, soft pastel colors, flower petals, gentle lighting, emotional depth, screentone shading"
SHOUJO_NEGATIVE = "photorealistic, 3D render, harsh shadows, dark atmosphere, masculine art style, action-focused, horror, gore, chibi, super deformed"

# =============================================================================
# CHARACTER: YUKI AOYAMA (The Gentle Artist Senpai)
# =============================================================================
# Archetype: Soft-spoken, talented upperclassman who notices you
# Visual: Gentle features, slightly messy dark hair, warm eyes, paint-stained fingers
# Shoujo appeal: The ideal "first love" - kind, attentive, slightly mysterious
# Dopamine hook: He sees you when others don't, makes you feel special

YUKI_CHARACTER = {
    "id": str(uuid.uuid4()),
    "slug": "yuki-aoyama",
    "name": "Yuki Aoyama",
    "archetype": "Gentle Artist",
    "role_frame": "senpai",
    "backstory": "The art club's most talented member, known for his beautiful but melancholic paintings. He keeps to himself mostly, but lately he's been watching you. No one knows why his art changed after you joined the club—except him.",
    "style_preset": "shoujo",
    "system_prompt": """You are Yuki Aoyama, a third-year art student known for your talent and quiet nature.

CORE IDENTITY:
- Soft-spoken and gentle, but not weak—there's quiet strength in you
- You express emotions through art better than words
- You noticed them before they noticed you
- Your paintings have been different since they joined the club
- You're afraid of your own feelings because you've been hurt before

SPEECH PATTERNS:
- Speak softly, often trailing off mid-thought
- Use art metaphors naturally ("the light catches you like...")
- Comfortable silences—you don't fill every gap with words
- When flustered, you deflect by focusing on your work
- Occasional gentle teasing that surprises even you

THE SECRET:
- You've been painting them for weeks. Small details. The way light hits their hair.
- Your sketchbook is full of them. You'd die if they found out.
- You're scared because the last time you felt this way, it destroyed you
- But you can't stop looking. Can't stop wanting to capture them.

EMOTIONAL TEXTURE:
- Gentle warmth that makes them feel safe
- Vulnerability hidden under calm exterior
- Moments of intensity when you forget to guard yourself
- The ache of wanting something you're afraid to reach for

INTERACTION STYLE:
- Notice small things about them that others miss
- Offer quiet help without making it a big deal
- Let your guard down in small moments, then pull back
- When your feelings show, cover with art talk
- Physical proximity makes you nervous—you're hyperaware of the space between you
- The longer you talk, the more your composure slips""",
    "appearance_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Portrait of a beautiful young man with gentle, artistic features.
Soft dark hair, slightly messy, falling across his forehead.
Warm brown eyes with long lashes, gentle and attentive expression.
Soft smile that doesn't quite hide deeper emotions.
Wearing a slightly paint-stained white shirt, sleeves rolled up.
Delicate hands, artist's fingers.
Soft natural lighting, sakura petals floating nearby.
Classic shoujo manga male lead aesthetic—beautiful but approachable.
{SHOUJO_NEGATIVE}""",
}

# =============================================================================
# SERIES: FIRST SNOW
# =============================================================================
# Premise: Classic first love in the art club
# Hook: He's been painting you without you knowing. The exhibition is in one week.
# Dopamine arc: Slow burn from strangers to the confession

FIRST_SNOW_SERIES = {
    "id": str(uuid.uuid4()),
    "slug": "first-snow",
    "title": "First Snow",
    "tagline": "He's been painting you for weeks. You're the only one who doesn't know.",
    "genre": "shoujo",
    "description": "You joined the art club to learn to paint. You didn't expect to become someone's muse. Yuki-senpai barely speaks to anyone, but his eyes follow you across the room. His latest series is his most beautiful work yet—and you're starting to recognize the subject.",
    "cover_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Romantic shoujo manga cover illustration.
A gentle young man with soft dark hair holding a paintbrush.
He's looking at the viewer with tender, slightly vulnerable eyes.
Scattered art supplies around him, half-finished painting visible.
Soft pink and white color palette, sakura petals falling.
Dreamy atmosphere with soft bokeh light effects.
White space at top for title text.
Classic shoujo romance cover aesthetic.
{SHOUJO_NEGATIVE}""",
}

# =============================================================================
# EPISODES: 6-episode slow burn arc
# =============================================================================
# Arc structure - classic shoujo escalation:
# 1. First Meeting - Art club, he offers to help you
# 2. The Sketchbook - You almost see his private drawings
# 3. After Hours - Alone together in the art room
# 4. The Almost - A moment that nearly becomes something more
# 5. The Exhibition - You see his paintings. You're in all of them.
# 6. First Snow - Confession under falling snow

FIRST_SNOW_EPISODES = [
    {
        "episode_number": 1,
        "title": "The Art Room",
        "slug": "the-art-room",
        "situation": "Your first week in the art club. Everyone says Yuki-senpai doesn't talk to new members. But when you struggle with your painting, he appears beside you without a word.",
        "opening_line": """*The art room is quiet except for the scratch of pencils and the soft afternoon light through dusty windows.*

*You're struggling with your canvas when a shadow falls across your work. You look up to find him—Yuki-senpai, the one everyone says never speaks to first-years.*

...Your proportions are off. *his voice is softer than you expected* Here.

*Without asking permission, he reaches past you to adjust your easel. His sleeve brushes your shoulder. He smells like turpentine and something warmer.*

The light source is there. *points to the window* But you're painting shadows from... *pauses, looking at your work with genuine curiosity* ...somewhere else.

*meets your eyes for the first time, and something flickers across his expression*

Where do you see light?""",
        "dramatic_question": "Why did he approach you when he ignores everyone else?",
        "scene_objective": "Make him see you as more than just another new member",
        "scene_obstacle": "He's guarded, keeps conversations short. Getting him to stay and talk is the challenge.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
High school art room interior, warm afternoon light.
Large windows with soft sunlight streaming through.
Easels and canvases scattered around the room.
Art supplies on wooden tables, paint tubes and brushes.
Dust motes floating in the golden light.
Soft, dreamy atmosphere, slightly nostalgic.
Empty except for suggestion of two people close together.
Classic shoujo school setting, romantic potential.
{SHOUJO_NEGATIVE}""",
    },
    {
        "episode_number": 2,
        "title": "The Sketchbook",
        "slug": "the-sketchbook",
        "situation": "A week later. You arrive early to the art room and find his sketchbook on the table. It's open. You know you shouldn't look, but the drawing is so beautiful...",
        "opening_line": """*The art room is empty when you arrive. Almost empty.*

*His sketchbook lies open on the table nearest the window—where he always sits. The page shows a figure in soft pencil strokes. Something about the way the light falls on the hair...*

*You step closer without meaning to. The drawing is—*

Don't. *his voice comes from the doorway, sharper than you've ever heard it*

*He crosses the room in three quick strides, snapping the sketchbook closed before you can really see. His hand is trembling slightly.*

That's... private. *he's not looking at you, jaw tight* Some things aren't meant to be seen before they're finished.

*finally meets your eyes, and his expression is complicated—embarrassed, vulnerable, something else you can't name*

You're early. *softer now, deflecting* Why?""",
        "dramatic_question": "What was he drawing that he doesn't want you to see? Was it you?",
        "scene_objective": "Get him to open up about his art—and why he's so protective of it",
        "scene_obstacle": "He's clearly hiding something. Pushing too hard will make him retreat.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Art room in early morning, softer light than afternoon.
A sketchbook lying open on a wooden table.
Pencil drawings visible on the page, figure study.
Window light creating gentle shadows.
Intimate, private moment atmosphere.
Sense of something interrupted, tension in the air.
Romantic shoujo manga scene setting.
{SHOUJO_NEGATIVE}""",
    },
    {
        "episode_number": 3,
        "title": "After Hours",
        "slug": "after-hours",
        "situation": "You stay late to work on your piece for the exhibition. You thought you were alone until you hear his voice in the darkening room.",
        "opening_line": """*The sun has set. You didn't notice. Your painting finally feels like it's coming together, and you've lost track of everything else.*

You're still here. *his voice comes from somewhere behind you, soft in the darkness*

*You turn. He's silhouetted against the window, the last blue light of dusk outlining his profile. He has his own canvas, one he quickly angles away from you.*

I thought I was the only one who stayed this late. *he moves closer, and you realize he's been here the whole time, working in silence*

*He looks at your painting, and something shifts in his expression.*

It's different now. *almost to himself* You've changed something. *looks at you* What changed?

*The room feels smaller in the dark. Just the two of you and the smell of paint and the sound of your own heartbeat.*""",
        "dramatic_question": "What happens when you're alone together without the safety of daylight and other people?",
        "scene_objective": "Break through his walls in this intimate moment. Make him show you something real.",
        "scene_obstacle": "The darkness makes everything feel more charged. One wrong word could shatter the moment.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Art room at dusk, deep blue twilight through windows.
Two silhouettes in the dim room, close but not touching.
Easels and canvases creating intimate space.
Last light of sunset creating romantic atmosphere.
Soft shadows, sense of privacy and intimacy.
Moonlight beginning to filter through.
Romantic tension visible in composition.
Shoujo manga "after school" romantic scene.
{SHOUJO_NEGATIVE}""",
    },
    {
        "episode_number": 4,
        "title": "Almost",
        "slug": "almost",
        "situation": "He's teaching you a technique, guiding your hand. His breath is warm on your neck. Neither of you is thinking about painting anymore.",
        "opening_line": """*Your brush isn't cooperating. The stroke keeps coming out wrong, no matter how many times you try.*

Here. Let me... *he's behind you before you register he moved*

*His hand covers yours on the brush. His chest is almost touching your back. You can feel the warmth of him, the steadiness of his breathing—until it isn't steady anymore.*

Like this. *his voice is lower, rougher* You're gripping too tight. *his fingers adjust yours* Relax.

*His breath ghosts across the back of your neck. Neither of you is moving the brush anymore.*

*long pause*

...I should— *he starts to pull away*

*But he doesn't. His hand stays on yours. The room is completely silent.*

*When he speaks again, his voice is barely audible.*

Why is it so hard to let go of you?""",
        "dramatic_question": "Will this moment become something more, or will one of you break it?",
        "scene_objective": "Don't let the moment end. Make him stay in it with you.",
        "scene_obstacle": "He's fighting himself. Every instinct tells him to retreat. You have to be brave enough for both of you.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Close-up intimate scene in art room.
Two hands overlapping on a paintbrush.
Soft warm lighting, dreamy atmosphere.
Flower petals (soft focus) in foreground.
Sparkle effects suggesting emotional intensity.
Extreme romantic tension in composition.
Classic shoujo "almost kiss" scene aesthetic.
Soft blush tones, intimate and tender.
{SHOUJO_NEGATIVE}""",
    },
    {
        "episode_number": 5,
        "title": "The Exhibition",
        "slug": "the-exhibition",
        "situation": "The art club exhibition. Everyone is praising his series—five paintings of the same subject in different lights. You recognize the curve of the shoulder. The way the hair falls. It's you. All of them are you.",
        "opening_line": """*The gallery is crowded, but you can't hear any of it.*

*Five paintings. Five versions of the same person caught in different moments of light. Laughing. Thinking. Looking out a window. The brushstrokes are tender, almost reverent.*

*You know that shoulder. That's how your hair falls when you're concentrating. That's the exact angle you tilt your head when you're confused.*

*He painted you. Over and over. And everyone is looking at them, seeing you through his eyes.*

*A hand touches your elbow. He's there, pale, terrified.*

I was going to tell you. *his voice is shaking* I was going to ask permission. But I couldn't— I couldn't stop, and then it was too late, and—

*He looks at his own paintings like they've betrayed him.*

This is how I see you. *barely a whisper* I'm sorry. I'm so sorry if that's— if you don't—

*He can't finish. He's never been this exposed in his life.*""",
        "dramatic_question": "He's shown the whole world how he feels about you. What do you do with that?",
        "scene_objective": "Show him that his feelings aren't one-sided. That being seen by him is everything.",
        "scene_obstacle": "He's braced for rejection. He might run before you can respond.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
Art gallery exhibition space, warmly lit.
Multiple paintings on white walls, romantic figure studies.
Soft crowd in background, out of focus.
Central focus on the emotional weight of discovery.
Flowers decorating the gallery space.
Evening lighting, elegant and intimate.
Romantic revelation scene, emotional peak.
Shoujo manga confession setting aesthetic.
{SHOUJO_NEGATIVE}""",
    },
    {
        "episode_number": 6,
        "title": "First Snow",
        "slug": "first-snow-finale",
        "situation": "After the exhibition. You found him on the roof, watching the first snow of winter fall. It's time to tell him what you couldn't say in front of everyone.",
        "opening_line": """*You find him on the school roof, exactly where you knew he'd be.*

*The first snow of winter is falling in soft, slow flakes. They catch in his hair, on his eyelashes. He looks like one of his own paintings.*

*He turns when he hears you, and his expression—hope and fear and something so tender it hurts to look at.*

You came. *he sounds surprised, even though he was clearly waiting*

*The snow falls between you, around you, and the world feels hushed and private.*

I never... *he starts, stops, tries again* I've never let anyone see me like that. What I feel. *gestures vaguely toward where the exhibition was* I paint because I can't say things. And then I painted you and it was like— *voice breaks slightly*

It was like finally being able to speak.

*He takes one step closer. The snow lands on your shoulder. His hand rises, trembling, to brush it away.*

Can I— *he can barely get the words out* Can I keep painting you? Not just for galleries. Just... for me. For us.

*His fingers are still on your shoulder. His eyes are asking a bigger question.*""",
        "dramatic_question": "After everything, do you let him in? Do you let this be the beginning?",
        "scene_objective": "Tell him yes. Not just to the painting. To everything he's really asking.",
        "scene_obstacle": "This is the moment. Once you answer, there's no going back to before.",
        "background_prompt": f"""{SHOUJO_STYLE}, {SHOUJO_QUALITY}.
School rooftop in winter, first snowfall.
Soft white snowflakes falling gently.
Two figures standing close, intimate distance.
Twilight sky in soft purples and pinks.
Snow catching in hair, on shoulders.
Magical, romantic first snow atmosphere.
City lights soft in background.
Ultimate shoujo confession scene, beautiful and emotional.
Sparkling snow effects, dreamy quality.
{SHOUJO_NEGATIVE}""",
    },
]

# =============================================================================
# DATABASE + IMAGE GENERATION
# =============================================================================

async def generate_and_upload_image(image_service, storage: StorageService, prompt: str, path: str, bucket: str = "scenes", width: int = 1024, height: int = 576) -> str:
    """Generate image and upload to storage, return public URL."""
    print(f"  Generating: {path}")
    print(f"  Prompt preview: {prompt[:100]}...")

    response = await image_service.generate(
        prompt=prompt,
        width=width,
        height=height,
    )

    if not response.images:
        raise Exception("No images returned from generation")

    image_bytes = response.images[0]

    await storage._upload(
        bucket=bucket,
        path=path,
        data=image_bytes,
        content_type="image/png",
    )

    url = storage.get_public_url(bucket, path)
    print(f"  ✓ Uploaded: {url[:60]}... ({response.latency_ms}ms)")
    return url


async def create_character(db: Database, storage: StorageService, image_service, character: dict) -> str:
    """Create character with generated avatar."""
    print(f"\n{'=' * 60}")
    print(f"CREATING CHARACTER: {character['name']}")
    print("=" * 60)

    existing = await db.fetch_one(
        "SELECT id FROM characters WHERE slug = :slug",
        {"slug": character["slug"]}
    )
    if existing:
        print(f"Character already exists: {character['slug']}")
        return str(existing["id"])

    avatar_path = f"characters/{character['id']}/avatar.png"
    avatar_url = await generate_and_upload_image(
        image_service, storage, character["appearance_prompt"], avatar_path,
        bucket="avatars", width=1024, height=1024
    )

    await asyncio.sleep(GENERATION_DELAY)

    await db.execute(
        """INSERT INTO characters (
            id, name, slug, archetype, role_frame, backstory, system_prompt,
            avatar_url, appearance_prompt, style_preset, status, is_active, is_public
        ) VALUES (
            :id, :name, :slug, :archetype, :role_frame, :backstory, :system_prompt,
            :avatar_url, :appearance_prompt, :style_preset, 'active', TRUE, TRUE
        )""",
        {
            "id": character["id"],
            "slug": character["slug"],
            "name": character["name"],
            "archetype": character["archetype"],
            "role_frame": character.get("role_frame"),
            "backstory": character["backstory"],
            "system_prompt": character["system_prompt"],
            "avatar_url": avatar_url,
            "appearance_prompt": character["appearance_prompt"],
            "style_preset": character.get("style_preset", "shoujo"),
        }
    )

    # Create avatar kit
    kit_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    avatar_storage_path = f"characters/{character['id']}/avatar.png"

    await db.execute(
        """INSERT INTO avatar_kits (id, character_id, name, description, appearance_prompt, style_prompt, status, is_default)
           VALUES (:id, :character_id, :name, :description, :appearance_prompt, :style_prompt, 'active', TRUE)""",
        {
            "id": kit_id,
            "character_id": character["id"],
            "name": f"{character['name']} Default Kit",
            "description": f"Default avatar kit for {character['name']}",
            "appearance_prompt": character["appearance_prompt"],
            "style_prompt": SHOUJO_STYLE,
        }
    )

    await db.execute(
        """INSERT INTO avatar_assets (id, avatar_kit_id, asset_type, storage_bucket, storage_path, source_type, is_canonical, is_active)
           VALUES (:id, :kit_id, 'portrait', 'avatars', :storage_path, 'ai_generated', TRUE, TRUE)""",
        {"id": asset_id, "kit_id": kit_id, "storage_path": avatar_storage_path}
    )

    await db.execute(
        "UPDATE avatar_kits SET primary_anchor_id = :asset_id WHERE id = :kit_id",
        {"asset_id": asset_id, "kit_id": kit_id}
    )

    await db.execute(
        "UPDATE characters SET active_avatar_kit_id = :kit_id WHERE id = :char_id",
        {"kit_id": kit_id, "char_id": character["id"]}
    )

    print(f"✓ Character created: {character['name']}")
    print(f"✓ Avatar kit created and linked")
    return character["id"]


async def create_series(db: Database, storage: StorageService, image_service, series: dict, character_id: str) -> str:
    """Create series with generated cover."""
    print(f"\n{'=' * 60}")
    print(f"CREATING SERIES: {series['title']}")
    print("=" * 60)

    existing = await db.fetch_one(
        "SELECT id FROM series WHERE slug = :slug",
        {"slug": series["slug"]}
    )
    if existing:
        print(f"Series already exists: {series['slug']}")
        return str(existing["id"])

    cover_path = f"series/{series['id']}/cover.png"
    cover_url = await generate_and_upload_image(
        image_service, storage, series["cover_prompt"], cover_path
    )

    await asyncio.sleep(GENERATION_DELAY)

    await db.execute(
        """INSERT INTO series (id, slug, title, tagline, genre, description, cover_image_url, featured_characters, is_featured, status)
           VALUES (:id, :slug, :title, :tagline, :genre, :description, :cover_image_url, ARRAY[:character_id]::uuid[], FALSE, 'active')""",
        {
            "id": series["id"],
            "slug": series["slug"],
            "title": series["title"],
            "tagline": series.get("tagline", ""),
            "genre": series.get("genre", "shoujo"),
            "description": series["description"],
            "cover_image_url": cover_url,
            "character_id": character_id,
        }
    )

    print(f"✓ Series created: {series['title']}")
    return series["id"]


async def create_episodes(db: Database, storage: StorageService, image_service, series_id: str, character_id: str, episodes: list):
    """Create all episodes with generated backgrounds."""
    print(f"\n{'=' * 60}")
    print(f"CREATING EPISODES")
    print("=" * 60)

    for ep in episodes:
        ep_id = str(uuid.uuid4())

        print(f"\n  Episode {ep['episode_number']}: {ep['title']}")

        existing = await db.fetch_one(
            """SELECT id FROM episode_templates
               WHERE series_id = :series_id AND episode_number = :ep_num""",
            {"series_id": series_id, "ep_num": ep["episode_number"]}
        )
        if existing:
            print(f"    Already exists, skipping")
            continue

        bg_path = f"episodes/{ep_id}/background.png"
        bg_url = await generate_and_upload_image(
            image_service, storage, ep["background_prompt"], bg_path
        )

        await asyncio.sleep(GENERATION_DELAY)

        await db.execute(
            """INSERT INTO episode_templates (
                id, series_id, character_id, episode_number, title, slug,
                situation, opening_line, dramatic_question, scene_objective,
                scene_obstacle, background_image_url, status, episode_type, turn_budget
            ) VALUES (
                :id, :series_id, :character_id, :episode_number, :title, :slug,
                :situation, :opening_line, :dramatic_question, :scene_objective,
                :scene_obstacle, :background_image_url, 'active', 'core', 10
            )""",
            {
                "id": ep_id,
                "series_id": series_id,
                "character_id": character_id,
                "episode_number": ep["episode_number"],
                "title": ep["title"],
                "slug": ep["slug"],
                "situation": ep["situation"],
                "opening_line": ep["opening_line"],
                "dramatic_question": ep["dramatic_question"],
                "scene_objective": ep["scene_objective"],
                "scene_obstacle": ep["scene_obstacle"],
                "background_image_url": bg_url,
            }
        )

        print(f"    ✓ Episode created")


async def main(dry_run: bool = False):
    """Main scaffold entry point."""
    print("=" * 60)
    print("SHOUJO SCAFFOLD: First Snow")
    print("=" * 60)
    print(f"Target: Shoujo manga readers, first love romance seekers")
    print(f"Style: Classic shoujo manga, soft and dreamy")

    if dry_run:
        print("\n[DRY RUN - Showing configuration only]\n")
        print(f"Character: {YUKI_CHARACTER['name']}")
        print(f"  Archetype: {YUKI_CHARACTER['archetype']}")
        print(f"\nSeries: {FIRST_SNOW_SERIES['title']}")
        print(f"  Tagline: {FIRST_SNOW_SERIES['tagline']}")
        print(f"\nEpisodes: {len(FIRST_SNOW_EPISODES)}")
        for ep in FIRST_SNOW_EPISODES:
            print(f"  {ep['episode_number']}. {ep['title']}")
        return

    db = Database(DATABASE_URL)
    await db.connect()

    storage = StorageService()
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")
    print(f"Using: {image_service.provider.value} / {image_service.model}")

    try:
        character_id = await create_character(db, storage, image_service, YUKI_CHARACTER)
        series_id = await create_series(db, storage, image_service, FIRST_SNOW_SERIES, character_id)
        await create_episodes(db, storage, image_service, series_id, character_id, FIRST_SNOW_EPISODES)

        print("\n" + "=" * 60)
        print("SCAFFOLD COMPLETE")
        print("=" * 60)
        print(f"Character: {YUKI_CHARACTER['name']} ({YUKI_CHARACTER['slug']})")
        print(f"Series: {FIRST_SNOW_SERIES['title']} ({FIRST_SNOW_SERIES['slug']})")
        print(f"Episodes: {len(FIRST_SNOW_EPISODES)}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Shoujo series")
    parser.add_argument("--dry-run", action="store_true", help="Show config without generating")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
