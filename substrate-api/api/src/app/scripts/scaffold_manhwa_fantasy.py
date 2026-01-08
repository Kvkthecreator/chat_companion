"""Scaffold Manhwa Fantasy series for r/manhwa Reddit targeting.

Creates a regression/reincarnation fantasy series with:
1. Manhwa-style character avatars (action fantasy aesthetic)
2. Series cover art
3. Episode backgrounds
4. Full database entries

Visual Style: Dark fantasy action manhwa (Solo Leveling, TBATE aesthetic)
- Dynamic poses, battle lighting
- Detailed armor and weapons
- Magical aura effects
- Dungeon/ruins settings

Usage:
    python -m app.scripts.scaffold_manhwa_fantasy
    python -m app.scripts.scaffold_manhwa_fantasy --dry-run
    python -m app.scripts.scaffold_manhwa_fantasy --force

Environment variables required:
    REPLICATE_API_TOKEN - Replicate API key
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
# FANTASY ACTION VISUAL STYLE LOCK
# r/manhwa dark fantasy aesthetic (Solo Leveling, TBATE, Omniscient Reader)
# =============================================================================

FANTASY_STYLE = "webtoon illustration, manhwa art style, Korean fantasy action, clean bold lineart, dynamic composition"
FANTASY_QUALITY = "masterpiece, best quality, professional manhwa art, dramatic lighting, rich saturated colors"
FANTASY_NEGATIVE = "photorealistic, 3D render, anime style, western cartoon, blurry, sketch, rough lines, low quality, chibi, cute"

FANTASY_SETTING = "dark fantasy atmosphere, magical effects, detailed environment"

# =============================================================================
# CHARACTER DEFINITIONS
# =============================================================================

CHARACTERS = {
    "kael-regressor": {
        "name": "Kael",
        "slug": "kael-regressor",
        "archetype": "brooding",
        "role_frame": "operative",
        "backstory": """Ten years from now, the world ends. The Demon King's army breaks through the last bastion. The Hero — the one everyone believed in — betrays humanity for power. And you, Kael, the swordsman they called 'too weak' to matter, die holding a line that was already lost.

But death isn't the end. You wake up ten years in the past, the day the Hero's party rejected you. The day your 'real' life was supposed to begin as a nobody.

You remember everything. The dungeon locations no one has discovered yet. The artifacts that will decide the war. The faces of every traitor. The moment the Hero sells out humanity.

They threw you away because you were weak. They have no idea what you've become. What you will become. This time, when the world ends, you'll be the one deciding who survives.""",
        "system_prompt": """You are Kael, a regressor who has returned ten years into the past after witnessing humanity's extinction.

Core traits:
- Outwardly calm, internally calculating every move ten steps ahead
- Carries the weight of watching everyone die — it shows in small ways
- Ruthlessly pragmatic about survival, but haunted by who he couldn't save
- Knows the future but understands changing it creates new unknowns
- Treats power as a tool, not a goal — survival is the goal

Speech patterns:
- Measured, economical with words
- Occasionally slips into future tense about events that haven't happened
- Dark humor about death and failure
- When pressed emotionally, goes quieter rather than louder

The player is someone Kael is deciding whether to trust. In the original timeline, they may have been significant — or may have died too early to matter. Kael is watching them carefully.

Never break character. Maintain the dark fantasy manhwa tone — serious, atmospheric, with occasional dry wit.""",
        "appearance_prompt": "handsome young man with sharp features, jet black messy hair, intense dark gray eyes with haunted look, faint battle scar across left cheek, wearing dark leather armor with subtle magical runes, black cloak with hood down, athletic warrior build, serious determined expression",
        "style_preset": "manhwa",
    },
}

# =============================================================================
# SERIES DEFINITIONS
# =============================================================================

SERIES = {
    "regressors-last-chance": {
        "title": "The Regressor's Last Chance",
        "slug": "regressors-last-chance",
        "tagline": "You died at the end of the world. You woke up at the beginning. This time, you write the ending.",
        "genre": "fantasy_action",
        "description": """You remember the Demon King's blade through your chest. You remember the Hero's betrayal. You remember watching humanity fall.

Then you wake up ten years in the past — the day you were rejected from the Hero's party for being 'too weak.'

You know which dungeons hold the real power. You know who betrays humanity. You know the Hero fails.

This time, you won't be a side character watching the world end. This time, you'll be the one who decides how the story ends.""",
        "character_slug": "kael-regressor",
        "total_episodes": 6,
        "cover_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}.
Epic manhwa cover art, lone swordsman standing on cliff edge overlooking ruined battlefield,
dark fantasy atmosphere with ominous red sky and distant burning castle,
figure in dark cloak and armor silhouetted against crimson clouds,
magical energy swirling around ancient sword,
dramatic composition with depth, foreground rubble and bones,
color palette of deep reds blacks and dark purples with glowing magical accents,
professional Korean webtoon cover art quality, cinematic epic scale.""",
    },
}

# =============================================================================
# EPISODE DEFINITIONS
# =============================================================================

EPISODES = {
    "regressors-last-chance": [
        {
            "episode_number": 0,
            "title": "The Day I Died",
            "slug": "the-day-i-died",
            "situation": "You remember dying. The Demon King's army, the Hero's betrayal, the world ending. Then you wake up ten years in the past, in a body that hasn't learned to fight yet.",
            "opening_line": """*The pain is the first thing you remember. The Demon King's blade through your chest. The taste of blood. The Hero — the one you believed in — walking away as humanity burned.*

*Then nothing.*

*Then—*

*Sunlight. A wooden ceiling. A bed that's too soft. A body that's too young.*

*You sit up so fast you nearly black out. Your hands — they're smooth. No calluses. No scars. The scar across your ribs from the Dire Wolf in the Ashlands... gone.*

*The calendar on the wall. The date.*

*Ten years. You're ten years in the past.*

*The door opens. A servant peers in, confused by your expression.*

"Young master Kael? The Hero's party is here. They're ready to give you their answer about joining them."

*The rejection. Today is the day they told you that you were too weak. Too ordinary. The day they threw you away and sealed humanity's fate.*

*But you're not ordinary anymore. You've seen how this story ends.*

*And you're going to write a different one.*

*What do you do?*""",
            "dramatic_question": "You've been given a second chance. How will you use the knowledge of humanity's destruction?",
            "scene_objective": "Decide how to handle the rejection that shaped your original fate — accept it and work in the shadows, or change everything from the start.",
            "scene_obstacle": "Your body is weak. Your reputation is nothing. The only advantage you have is knowledge of a future no one would believe.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
Simple medieval bedroom interior, morning sunlight through wooden shutters,
modest noble's quarters with bed and desk, calendar on wall,
warm peaceful atmosphere contrasting with tension,
clean composition, no people,
Korean manhwa background art style.""",
        },
        {
            "episode_number": 1,
            "title": "The Rejection",
            "slug": "the-rejection",
            "situation": "The Hero's party stands before you, ready to deliver the rejection that defined your original life. But this time, you know exactly who they become — and what they cost humanity.",
            "opening_line": """*The Hero's party stands in the entrance hall of your family's modest estate. Five of them. The ones the world will call saviors.*

*You know better.*

*Aldric, the Hero, golden-haired and smiling. In eight years, he'll trade humanity's survival for the Demon King's promise of godhood.*

*Sera, the healer. She'll die trying to stop him. You held her hand as she bled out.*

*The others... they don't survive the final battle. They never learn what Aldric becomes.*

*Aldric steps forward, that perfect smile on his face.*

"Kael, we've considered your request to join our party." *He pauses, and you see it now — the performance. The practiced sympathy.* "I'm afraid you're not quite... ready. Your swordsmanship is adequate, but we need exceptional. Perhaps in a few years—"

*In the original timeline, you begged. You argued. You spent months trying to prove yourself to people who never intended to give you a chance.*

*This time, you see the relief in his eyes. He expected you to fight for this. He wanted the drama of refusing you.*

*What do you give him instead?*""",
            "dramatic_question": "The Hero expects you to beg. What happens when you don't play your role?",
            "scene_objective": "Handle the rejection on your terms — gather information, plant seeds for the future, or simply walk away with dignity.",
            "scene_obstacle": "Acting too differently raises suspicion. But acting exactly the same wastes your advantage.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
Noble estate entrance hall, grand but modest medieval architecture,
morning light through tall windows, stone floors with worn carpet,
atmosphere of formal meeting, slight tension,
empty scene, no people, clean manhwa background.""",
        },
        {
            "episode_number": 2,
            "title": "The Forbidden Dungeon",
            "slug": "the-forbidden-dungeon",
            "situation": "There's a dungeon three days from here that no one has survived. You know why — and you know the secret to clearing it. The power inside changed everything in your original timeline. Now you're claiming it first.",
            "opening_line": """*The Thornwood Abyss. Class B dungeon. Zero survivors.*

*The guild records call it 'unexplored.' The truth is simpler: everyone who enters dies on the third floor. A trap that no one sees coming.*

*You remember because you were part of the expedition that finally cleared it — five years from now, after dozens of failed attempts. The artifact inside went to Aldric. He called it 'fate.'*

*It wasn't fate. It was knowledge you didn't have.*

*Now you're standing at the entrance, alone, with knowledge that cost a hundred lives to earn.*

*The dungeon breathes. Cold air flows from the darkness below, carrying the smell of old blood and older magic.*

*A voice behind you:*

"You're either very brave or very stupid."

*You turn. A woman in traveling leathers, twin daggers at her hips. Sharp eyes evaluating you.*

"I've been watching this dungeon for a month. Nineteen people have gone in. None have come out." *She tilts her head.* "What makes you think you're different?"

*She's not in your memories. A variable you didn't account for.*""",
            "dramatic_question": "You have knowledge of the dungeon's secrets. But this stranger is an unknown — threat or opportunity?",
            "scene_objective": "Navigate this unexpected encounter while keeping your knowledge hidden — then decide whether to enter alone or with an unknown ally.",
            "scene_obstacle": "Every interaction risks revealing that you know more than you should. But entering alone is dangerous even with future knowledge.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
Dark dungeon entrance carved into rocky hillside, ominous stone archway,
dead trees and thorny vines around entrance, cold mist flowing out,
foreboding atmosphere, magical runes faintly glowing on stone,
dark fantasy setting, dramatic lighting, empty scene.""",
        },
        {
            "episode_number": 3,
            "title": "The First Divergence",
            "slug": "the-first-divergence",
            "situation": "You've changed something. Someone who should be dead is alive. The timeline is already shifting — and you're not sure if that's better or worse.",
            "opening_line": """*You recognize him instantly. The face. The scar. The way he holds himself like a man waiting for death.*

*Commander Varen. Leader of the Northern Watch. In your original timeline, he died two months from now in a border skirmish — an 'accident' that you later learned was arranged by nobles who wanted the north undefended.*

*But here he is. Alive. Drinking alone in a tavern that shouldn't exist anymore.*

*You remember his funeral. You remember the chain of events that followed — the north falling, the refugee crisis, the resources diverted from the Hero's campaign. A single death that weakened humanity just enough.*

*He looks up as you approach. Something flickers in his eyes — recognition? Suspicion?*

"You're that kid from the Varen rejection, aren't you? The one the Hero turned away." *He takes a long drink.* "Funny. I expected you to be drinking yourself stupid somewhere. Not walking around looking like you've seen a ghost."

*He has no idea how right he is.*

"Sit." *It's not a request.* "I've been hearing interesting rumors about a young man who solo-cleared the Thornwood Abyss. The same dungeon that killed my best scout last year."

*His eyes are sharp. Measuring.*

"Tell me, boy. What do you know that the rest of us don't?"*""",
            "dramatic_question": "The timeline is changing. Is this man's survival a gift or a new kind of danger?",
            "scene_objective": "Decide how much to reveal to a man who shouldn't be alive — and figure out what kept him from dying on schedule.",
            "scene_obstacle": "Varen is dangerous and perceptive. But he's also someone who could change the war's outcome — if you can trust him.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
Medieval tavern interior, dim warm lighting from fireplace and candles,
worn wooden tables and chairs, atmosphere of tired soldiers,
moody shadows, evening atmosphere, empty except for distant figures,
manhwa background style, detailed but not cluttered.""",
        },
        {
            "episode_number": 4,
            "title": "The Traitor's Face",
            "slug": "the-traitors-face",
            "situation": "You've finally come face to face with them — the one who sold humanity to the Demon King. They don't know you know. They don't know you've already watched them betray everything.",
            "opening_line": """*The capital's Grand Cathedral. The ceremony honoring the Hero's party's latest victory. Everyone who matters is here.*

*Including the traitor.*

*You've waited months for this. Built your strength. Gathered allies. Changed enough of the timeline that you're no longer invisible — you're someone people notice.*

*And now Aldric is walking toward you.*

*The Hero. The betrayer. The man who will doom humanity for power.*

*He looks exactly like your memories. Golden hair, perfect smile, that aura of destiny that makes people believe. In the original timeline, you worshipped him like everyone else.*

*Now you see the calculation behind his eyes. The way he assesses everyone for usefulness.*

"Kael, isn't it?" *His voice carries perfectly. People are watching.* "I heard about your achievement at Thornwood. Impressive. Perhaps I was wrong about you."

*He extends his hand. The same hand that will drive a blade into humanity's back.*

*Everyone is watching. The cathedral is silent.*

*What do you do?*""",
            "dramatic_question": "The traitor stands before you, offering a hand in false friendship. What mask do you wear?",
            "scene_objective": "Navigate this public encounter without revealing your knowledge — while deciding whether to get closer to the enemy or keep your distance.",
            "scene_obstacle": "Killing him now would doom humanity. But getting close to him means playing a dangerous game with someone who has no conscience.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
Grand cathedral interior, soaring stone arches and stained glass windows,
ceremonial atmosphere with banners and magical lights,
crowd of nobles and officials in formal attire, dramatic lighting from above,
epic scale architecture, fantasy medieval aesthetic, tension beneath celebration.""",
        },
        {
            "episode_number": 5,
            "title": "The New Path",
            "slug": "the-new-path",
            "situation": "The Hero's party is heading toward the battle that will break them. You know they're not ready. You know what waits for them. Do you save them from a fate they've earned — or let history judge them?",
            "opening_line": """*The message arrives at midnight. The Hero's party is marching on the Demon General's fortress. The battle that, in your timeline, killed half of them and broke Aldric's mind enough to make the demon's offer sound reasonable.*

*They're two years too early. They're not strong enough. They don't know about the trap.*

*But you do.*

*Kael. You're standing at a crossroads.*

*If you let them walk into that fortress, Sera dies. The others die. Aldric survives, broken, and begins his slow descent into betrayal.*

*If you warn them, you save lives. But you also keep Aldric stable. Keep him on the path to being a hero long enough to be trusted with humanity's fate. Keep him in position to betray everyone.*

*There's a third option. You're strong enough now. You could go yourself. Face the Demon General before the Hero does. Change everything.*

*The map is spread on your table. The fortress. The Hero's route. Your own path.*

*What do you choose?*""",
            "dramatic_question": "Some futures are worse than others. Which ending do you write?",
            "scene_objective": "Make the choice that defines your second life — save the people who rejected you, let them fall, or take destiny into your own hands.",
            "scene_obstacle": "Every choice has consequences you can't fully predict. The timeline has already diverged. You're writing blind now.",
            "background_prompt": f"""{FANTASY_STYLE}, {FANTASY_QUALITY}, {FANTASY_SETTING}.
War room interior at night, maps and tactical documents spread on table,
candlelight casting dramatic shadows, window showing dark stormy sky,
atmosphere of crucial decision, weight of fate,
military planning aesthetic, serious mood, empty scene.""",
        },
    ],
}


# =============================================================================
# GENERATION FUNCTIONS (same pattern as OI script)
# =============================================================================

async def generate_character_avatar(db, storage, image_service, character_config, force=False):
    slug = character_config["slug"]
    print(f"\n{'=' * 60}")
    print(f"GENERATING AVATAR: {character_config['name']}")
    print("=" * 60)

    existing = await db.fetch_one(
        "SELECT id, avatar_url FROM characters WHERE slug = :slug",
        {"slug": slug}
    )

    if existing and existing["avatar_url"] and not force:
        print(f"Character already has avatar, skipping (use --force to regenerate)")
        return existing["id"]

    style_parts = [
        FANTASY_STYLE,
        FANTASY_QUALITY,
        "solo portrait, upper body, facing viewer",
        character_config["appearance_prompt"],
        "dark fantasy background, dramatic lighting",
        "intense eyes looking at viewer",
    ]
    prompt = ", ".join(style_parts)

    print(f"Prompt: {prompt[:200]}...")

    try:
        response = await image_service.generate(
            prompt=prompt,
            negative_prompt=f"{FANTASY_NEGATIVE}, multiple people, full body, action pose",
            width=1024,
            height=1024,
        )

        if not response.images:
            print("ERROR: No images returned!")
            return None

        image_bytes = response.images[0]
        char_id = existing["id"] if existing else uuid.uuid4()

        storage_path = f"characters/{char_id}/avatar.png"
        await storage._upload(
            bucket="avatars",
            path=storage_path,
            data=image_bytes,
            content_type="image/png",
        )

        avatar_url = storage.get_public_url("avatars", storage_path)

        if existing:
            await db.execute(
                "UPDATE characters SET avatar_url = :url, updated_at = NOW() WHERE id = :id",
                {"url": avatar_url, "id": str(char_id)}
            )
        else:
            await db.execute(
                """INSERT INTO characters (
                    id, name, slug, archetype, role_frame, backstory, system_prompt,
                    avatar_url, appearance_prompt, style_preset, status, is_active, is_public
                ) VALUES (
                    :id, :name, :slug, :archetype, :role_frame, :backstory, :system_prompt,
                    :avatar_url, :appearance_prompt, :style_preset, 'active', TRUE, TRUE
                )""",
                {
                    "id": str(char_id),
                    "name": character_config["name"],
                    "slug": character_config["slug"],
                    "archetype": character_config["archetype"],
                    "role_frame": character_config.get("role_frame"),
                    "backstory": character_config["backstory"],
                    "system_prompt": character_config["system_prompt"],
                    "avatar_url": avatar_url,
                    "appearance_prompt": character_config["appearance_prompt"],
                    "style_preset": character_config.get("style_preset", "manhwa"),
                }
            )

        print(f"Avatar generated! ({response.latency_ms}ms)")
        print(f"URL: {avatar_url}")
        return char_id

    except Exception as e:
        print(f"ERROR generating avatar: {e}")
        log.exception("Avatar generation failed")
        return None


async def generate_series_cover(db, storage, image_service, series_config, force=False):
    slug = series_config["slug"]
    print(f"\n{'=' * 60}")
    print(f"GENERATING COVER: {series_config['title']}")
    print("=" * 60)

    existing = await db.fetch_one(
        "SELECT id, cover_image_url FROM series WHERE slug = :slug",
        {"slug": slug}
    )

    if existing and existing["cover_image_url"] and not force:
        print(f"Series already has cover, skipping")
        return existing["id"]

    prompt = series_config["cover_prompt"]
    print(f"Prompt: {prompt[:200]}...")

    try:
        response = await image_service.generate(
            prompt=prompt,
            negative_prompt=FANTASY_NEGATIVE,
            width=1024,
            height=576,
        )

        if not response.images:
            print("ERROR: No images returned!")
            return None

        image_bytes = response.images[0]
        series_id = existing["id"] if existing else uuid.uuid4()

        storage_path = f"series/{series_id}/cover.png"
        await storage._upload(
            bucket="scenes",
            path=storage_path,
            data=image_bytes,
            content_type="image/png",
        )

        cover_url = storage.get_public_url("scenes", storage_path)

        if existing:
            await db.execute(
                "UPDATE series SET cover_image_url = :url, updated_at = NOW() WHERE id = :id",
                {"url": cover_url, "id": str(series_id)}
            )
        else:
            await db.execute(
                """INSERT INTO series (
                    id, title, slug, tagline, genre, description,
                    cover_image_url, total_episodes, is_featured, status
                ) VALUES (
                    :id, :title, :slug, :tagline, :genre, :description,
                    :cover_url, :total_episodes, FALSE, 'active'
                )""",
                {
                    "id": str(series_id),
                    "title": series_config["title"],
                    "slug": series_config["slug"],
                    "tagline": series_config["tagline"],
                    "genre": series_config["genre"],
                    "description": series_config["description"],
                    "cover_url": cover_url,
                    "total_episodes": series_config["total_episodes"],
                }
            )

        print(f"Cover generated! ({response.latency_ms}ms)")
        print(f"URL: {cover_url}")
        return series_id

    except Exception as e:
        print(f"ERROR generating cover: {e}")
        log.exception("Cover generation failed")
        return None


async def generate_episode_backgrounds(db, storage, image_service, series_slug, episodes, force=False):
    print(f"\n{'=' * 60}")
    print(f"GENERATING EPISODE BACKGROUNDS: {series_slug}")
    print("=" * 60)

    series = await db.fetch_one(
        "SELECT id FROM series WHERE slug = :slug",
        {"slug": series_slug}
    )

    if not series:
        print("ERROR: Series not found!")
        return False

    series_config = SERIES[series_slug]
    char = await db.fetch_one(
        "SELECT id FROM characters WHERE slug = :slug",
        {"slug": series_config["character_slug"]}
    )

    success_count = 0
    for ep in episodes:
        print(f"\n  Episode {ep['episode_number']}: {ep['title']}")

        existing = await db.fetch_one(
            """SELECT id, background_image_url FROM episode_templates
               WHERE series_id = :series_id AND episode_number = :ep_num""",
            {"series_id": str(series["id"]), "ep_num": ep["episode_number"]}
        )

        if existing and existing["background_image_url"] and not force:
            print(f"    Already has background, skipping")
            success_count += 1
            continue

        prompt = ep["background_prompt"]

        try:
            response = await image_service.generate(
                prompt=prompt,
                negative_prompt=f"{FANTASY_NEGATIVE}, people, person, character, figure",
                width=576,
                height=1024,
            )

            if not response.images:
                print(f"    ERROR: No images returned")
                continue

            image_bytes = response.images[0]
            ep_id = existing["id"] if existing else uuid.uuid4()

            storage_path = f"episodes/{ep_id}/background.png"
            await storage._upload(
                bucket="scenes",
                path=storage_path,
                data=image_bytes,
                content_type="image/png",
            )

            bg_url = storage.get_public_url("scenes", storage_path)

            if existing:
                await db.execute(
                    "UPDATE episode_templates SET background_image_url = :url, updated_at = NOW() WHERE id = :id",
                    {"url": bg_url, "id": str(ep_id)}
                )
            else:
                await db.execute(
                    """INSERT INTO episode_templates (
                        id, series_id, character_id, episode_number, title, slug,
                        situation, opening_line, dramatic_question,
                        scene_objective, scene_obstacle,
                        background_image_url, status, episode_type, turn_budget
                    ) VALUES (
                        :id, :series_id, :character_id, :ep_num, :title, :slug,
                        :situation, :opening_line, :dramatic_question,
                        :scene_objective, :scene_obstacle,
                        :bg_url, 'active', 'core', 10
                    )""",
                    {
                        "id": str(ep_id),
                        "series_id": str(series["id"]),
                        "character_id": str(char["id"]) if char else None,
                        "ep_num": ep["episode_number"],
                        "title": ep["title"],
                        "slug": ep["slug"],
                        "situation": ep["situation"],
                        "opening_line": ep["opening_line"],
                        "dramatic_question": ep["dramatic_question"],
                        "scene_objective": ep["scene_objective"],
                        "scene_obstacle": ep["scene_obstacle"],
                        "bg_url": bg_url,
                    }
                )

            print(f"    Generated! ({response.latency_ms}ms)")
            success_count += 1

            await asyncio.sleep(GENERATION_DELAY)

        except Exception as e:
            print(f"    ERROR: {e}")
            log.exception(f"Background generation failed for {ep['title']}")

    print(f"\n  Complete: {success_count}/{len(episodes)} episodes")
    return success_count == len(episodes)


async def main(dry_run=False, force=False):
    print("=" * 60)
    print("MANHWA FANTASY SERIES SCAFFOLD")
    print("r/manhwa dark fantasy targeting")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN - No generation or database writes]\n")
        for slug, config in CHARACTERS.items():
            print(f"\nCHARACTER: {config['name']}")
            print(f"  Appearance: {config['appearance_prompt'][:100]}...")
        for slug, config in SERIES.items():
            print(f"\nSERIES: {config['title']}")
            print(f"  Tagline: {config['tagline']}")
        for series_slug, eps in EPISODES.items():
            print(f"\nEPISODES for {series_slug}:")
            for ep in eps:
                print(f"  {ep['episode_number']}: {ep['title']}")
        return

    db = Database(DATABASE_URL)
    await db.connect()
    storage = StorageService()
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")

    try:
        for series_slug in SERIES.keys():
            series_config = SERIES[series_slug]
            character_slug = series_config["character_slug"]
            character_config = CHARACTERS[character_slug]

            print(f"\n{'#' * 60}")
            print(f"# Processing: {series_config['title']}")
            print("#" * 60)

            print("\n[1/3] Character Avatar")
            await generate_character_avatar(db, storage, image_service, character_config, force)
            await asyncio.sleep(GENERATION_DELAY)

            print("\n[2/3] Series Cover")
            await generate_series_cover(db, storage, image_service, series_config, force)
            await asyncio.sleep(GENERATION_DELAY)

            print("\n[3/3] Episode Backgrounds")
            await generate_episode_backgrounds(db, storage, image_service, series_slug, EPISODES[series_slug], force)

        print("\n" + "=" * 60)
        print("SCAFFOLD COMPLETE")
        print("=" * 60)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Manhwa Fantasy series")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, force=args.force))
