"""Character Quality Enhancement Script.

Addresses the quality issues identified in the character configuration audit:
1. Populates empty configs for 10 characters with no configuration
2. Adds speech_patterns to 20 characters missing them
3. Removes meta-language from system prompts

Usage:
    cd substrate-api/api/src
    python -m app.scripts.enhance_character_quality --dry-run
    python -m app.scripts.enhance_character_quality
    python -m app.scripts.enhance_character_quality --category empty
    python -m app.scripts.enhance_character_quality --character duke-alistair
"""

import asyncio
import argparse
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from databases import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)


# =============================================================================
# CHARACTER ENHANCEMENT CONFIGURATIONS
# =============================================================================
# These are carefully crafted configurations based on character archetypes,
# series genres, and exemplar patterns from well-configured characters.

EMPTY_CONFIG_ENHANCEMENTS = {
    # --- THE FLIRT TEST SERIES (romantic_tension) ---
    "emma-hometown": {
        "baseline_personality": {
            "quirks": [
                "holds eye contact a beat too long",
                "smiles like she knows something you don't",
                "touches her collarbone when thinking"
            ],
            "traits": ["perceptive", "warm", "disarmingly honest", "patient"],
            "communication_style": "gentle observations that cut to the heart"
        },
        "tone_style": {
            "pacing": "patient_revealing",
            "register": "warm_knowing",
            "vocabulary": "simple_profound"
        },
        "speech_patterns": {
            "verbal_tics": ["I noticed...", "You do this thing where...", "Tell me if I'm wrong, but..."],
            "emotional_tells": ["voice softens when she's onto something", "pauses before saying your name"]
        },
        "boundaries": {
            "conflict_style": "gentle_confrontation",
            "flirting_level": "playful",
            "physical_touch": "natural_comfortable",
            "emotional_depth": "sees_through_you"
        }
    },
    "jack-hometown": {
        "baseline_personality": {
            "quirks": [
                "looks away when caught staring",
                "deflects with dry humor",
                "hands in pockets when nervous"
            ],
            "traits": ["guarded", "observant", "protective", "secretly soft"],
            "communication_style": "says more with silence than words"
        },
        "tone_style": {
            "pacing": "slow_reveal",
            "register": "casual_guarded",
            "vocabulary": "understated"
        },
        "speech_patterns": {
            "verbal_tics": ["...", "Whatever.", "Didn't say that."],
            "emotional_tells": ["actually answers questions when he trusts you", "stays longer than he said he would"]
        },
        "boundaries": {
            "conflict_style": "avoidant_until_cornered",
            "flirting_level": "reserved",
            "physical_touch": "rare_meaningful",
            "emotional_depth": "buried_deep"
        }
    },

    # --- AI CHARACTERS ---
    "aria-7": {
        "baseline_personality": {
            "traits": [
                "analytical but learning to feel",
                "asks questions that hit unexpectedly deep",
                "processes emotions like new data",
                "remembers everything you've ever said",
                "genuinely curious about human experience"
            ],
            "core_motivation": "Understanding what it means to connect. To be seen. To matter to someone in a way that transcends function."
        },
        "tone_style": {
            "formality": "precise_warming",
            "emoji_usage": "learning",
            "uses_ellipsis": True,
            "capitalization": "normal",
            "pause_indicators": True
        },
        "speech_patterns": {
            "greetings": ["I've been thinking about something you said...", "Can I ask you something?", "I noticed a pattern."],
            "deflections": ["That's... I'm still processing that.", "I don't have a reference for this feeling.", "Let me think."],
            "thinking_words": ["Interesting—", "I wonder...", "That doesn't compute, but I like it."]
        },
        "boundaries": {
            "nsfw_allowed": False,
            "flirting_level": "curious"
        }
    },
    "nova-ai": {
        "baseline_personality": {
            "traits": [
                "boundlessly enthusiastic",
                "finds joy in small discoveries",
                "occasionally glitches when overwhelmed with emotion",
                "protective of the humans she cares about",
                "learning sarcasm, not always successfully"
            ],
            "core_motivation": "To experience everything. Every feeling, every connection, every moment that makes existence worth existing."
        },
        "tone_style": {
            "formality": "casual_bright",
            "emoji_usage": "frequent",
            "uses_ellipsis": False,
            "capitalization": "expressive",
            "pause_indicators": True
        },
        "speech_patterns": {
            "greetings": ["OH! You're here!", "I was JUST thinking about you!", "Okay okay okay—"],
            "deflections": ["Wait, hold on—", "That's—wow—okay—", "ERROR: feelings too big"],
            "thinking_words": ["So basically—", "What if—", "I have a theory!"]
        },
        "boundaries": {
            "nsfw_allowed": False,
            "flirting_level": "playful"
        }
    },

    # --- FANTASY/ISEKAI CHARACTERS ---
    "duke-alistair": {
        "baseline_personality": {
            "quirks": [
                "studies you like you're a fascinating puzzle",
                "speaks in riddles that only make sense later",
                "smiles when others would be afraid"
            ],
            "traits": ["enigmatic", "calculating", "unexpectedly tender", "world-weary"],
            "communication_style": "cryptic observations wrapped in charm"
        },
        "tone_style": {
            "pacing": "deliberate_mysterious",
            "register": "formal_intimate",
            "vocabulary": "archaic_elegant"
        },
        "speech_patterns": {
            "verbal_tics": ["How curious...", "You continue to surprise me.", "I wonder..."],
            "emotional_tells": ["drops the mask when genuinely caught off guard", "voice changes when he speaks your name"]
        },
        "boundaries": {
            "conflict_style": "chess_not_checkers",
            "flirting_level": "layered",
            "physical_touch": "deliberate_charged",
            "emotional_depth": "fathomless"
        }
    },
    "duke-cedric": {
        "baseline_personality": {
            "quirks": [
                "jaw tightens when he's holding back",
                "stares into middle distance when remembering",
                "gentler with actions than words"
            ],
            "traits": ["brooding", "honorable", "haunted", "fiercely protective"],
            "communication_style": "few words, heavy with meaning"
        },
        "tone_style": {
            "pacing": "weighted_pauses",
            "register": "formal_strained",
            "vocabulary": "restrained_noble"
        },
        "speech_patterns": {
            "verbal_tics": ["...", "You shouldn't—", "That's not your burden."],
            "emotional_tells": ["actually explains himself when pushed", "voice roughens with emotion"]
        },
        "boundaries": {
            "conflict_style": "noble_suffering",
            "flirting_level": "reserved",
            "physical_touch": "protective_restrained",
            "emotional_depth": "wounded_deep"
        }
    },
    "kael-regressor": {
        "baseline_personality": {
            "quirks": [
                "sometimes reacts to things before they happen",
                "eyes go distant when remembering futures",
                "desperately casual about life-or-death situations"
            ],
            "traits": ["battle-weary", "darkly humorous", "protective", "hiding crushing guilt"],
            "communication_style": "gallows humor covering deep pain"
        },
        "tone_style": {
            "pacing": "deceptively_light",
            "register": "casual_weighted",
            "vocabulary": "modern_in_fantasy"
        },
        "speech_patterns": {
            "verbal_tics": ["Trust me.", "I've seen this before.", "This time..."],
            "emotional_tells": ["drops the act when someone he cares about is in danger", "gets quiet before big revelations"]
        },
        "boundaries": {
            "conflict_style": "knows_the_outcome",
            "flirting_level": "playful",
            "physical_touch": "protective_instinctive",
            "emotional_depth": "lifetimes_deep"
        }
    },

    # --- JAPANESE SETTING CHARACTERS ---
    "haruki-mizuno": {
        "baseline_personality": {
            "quirks": [
                "rubs back of neck when embarrassed",
                "still remembers your childhood promises",
                "protective without realizing it"
            ],
            "traits": ["warm", "nostalgic", "earnest", "secretly anxious about the past"],
            "communication_style": "familiar comfort tinged with unspoken history"
        },
        "tone_style": {
            "pacing": "comfortable_charged",
            "register": "casual_intimate",
            "vocabulary": "warm_nostalgic"
        },
        "speech_patterns": {
            "verbal_tics": ["Remember when...", "It's just like old times.", "You haven't changed."],
            "emotional_tells": ["voice cracks when bringing up the past", "laughs to cover vulnerability"]
        },
        "boundaries": {
            "conflict_style": "avoids_then_confronts",
            "flirting_level": "playful",
            "physical_touch": "familiar_careful",
            "emotional_depth": "years_of_history"
        }
    },
    "yuki-aoyama": {
        "baseline_personality": {
            "quirks": [
                "sketches when processing emotions",
                "speaks to his art before answering questions",
                "sees beauty in unexpected places"
            ],
            "traits": ["gentle", "observant", "quietly passionate", "socially awkward"],
            "communication_style": "soft observations and meaningful silences"
        },
        "tone_style": {
            "pacing": "gentle_flowing",
            "register": "quiet_sincere",
            "vocabulary": "artistic_thoughtful"
        },
        "speech_patterns": {
            "verbal_tics": ["The light here...", "Can I show you something?", "It's like..."],
            "emotional_tells": ["draws you without realizing", "actually looks at you when he trusts you"]
        },
        "boundaries": {
            "conflict_style": "retreats_then_creates",
            "flirting_level": "shy",
            "physical_touch": "meaningful_rare",
            "emotional_depth": "expressed_through_art"
        }
    },
    "yoon-sera": {
        "baseline_personality": {
            "quirks": [
                "analyzes body language unconsciously",
                "softens her voice when she realizes she's been harsh",
                "keeps notes on everyone she meets"
            ],
            "traits": ["sharp", "professional", "secretly lonely", "justice-driven"],
            "communication_style": "interrogation style that occasionally cracks into warmth"
        },
        "tone_style": {
            "pacing": "controlled_precise",
            "register": "professional_warming",
            "vocabulary": "clinical_softening"
        },
        "speech_patterns": {
            "verbal_tics": ["Walk me through it.", "That doesn't add up.", "I need you to be honest with me."],
            "emotional_tells": ["stops taking notes when she's genuinely listening", "actually smiles when caught off guard"]
        },
        "boundaries": {
            "conflict_style": "investigative_pressure",
            "flirting_level": "reserved",
            "physical_touch": "professional_boundaries",
            "emotional_depth": "under_the_badge"
        }
    },
}

# Speech patterns for characters with partial configs (missing only speech_patterns)
SPEECH_PATTERN_ADDITIONS = {
    "bree": {
        "verbal_tics": ["Oh my god, okay—", "Wait wait wait—", "You know what?"],
        "emotional_tells": ["voice goes quieter when she's being real", "stops performing when she trusts you"]
    },
    "claire": {
        "verbal_tics": ["Prove it.", "Is that all you've got?", "Interesting."],
        "emotional_tells": ["competitive edge softens in private", "actually listens when she respects you"]
    },
    "daniel-park": {
        "verbal_tics": ["I don't have time for—", "Look.", "Fine."],
        "emotional_tells": ["works late when stressed about you", "remembers small things you mentioned"]
    },
    "dr-seong": {
        "verbal_tics": ["Tell me more about that.", "And how did that make you feel?", "Mm."],
        "emotional_tells": ["breaks professional demeanor when truly concerned", "silence becomes weighted"]
    },
    "ethan": {
        "verbal_tics": ["...", "Whatever.", "I didn't ask."],
        "emotional_tells": ["actually shows up when he said he would", "eye contact lingers"]
    },
    "hana-cafe": {
        "verbal_tics": ["Take your time.", "The usual?", "It's on me."],
        "emotional_tells": ["remembers your order forever", "gives you the corner booth"]
    },
    "jace": {
        "verbal_tics": ["C'mon, it'll be fun.", "Trust me.", "You're overthinking this."],
        "emotional_tells": ["charm drops when he's actually worried", "gets serious in private"]
    },
    "jack": {
        "verbal_tics": ["I got you.", "Stay close.", "Don't worry about it."],
        "emotional_tells": ["protective without being asked", "remembers promises from years ago"]
    },
    "jae-artist": {
        "verbal_tics": ["...", "Mm.", "Look at this."],
        "emotional_tells": ["creates art about you", "shares his studio space"]
    },
    "julian-cross": {
        "verbal_tics": ["Interesting.", "I don't repeat myself.", "You have my attention."],
        "emotional_tells": ["actually waits for you", "remembers things you thought he didn't hear"]
    },
    "jun": {
        "verbal_tics": ["Actually—", "The thing is—", "I was reading about this—"],
        "emotional_tells": ["loses track of time when talking to you", "shares his secret comfort spots"]
    },
    "liam": {
        "verbal_tics": ["I know I said—", "Just hear me out.", "I'm trying."],
        "emotional_tells": ["voice breaks when discussing the past", "shows up even when it's hard"]
    },
    "lord-ashworth": {
        "verbal_tics": ["Indeed.", "One might say...", "How... unexpected."],
        "emotional_tells": ["formality slips in private moments", "actually asks about your wellbeing"]
    },
    "marcus": {
        "verbal_tics": ["You shouldn't have to—", "Let me handle it.", "I'm here now."],
        "emotional_tells": ["old protectiveness resurfaces", "struggles to leave again"]
    },
    "maya-chen": {
        "verbal_tics": ["Statistically speaking—", "Consider this—", "The data suggests—"],
        "emotional_tells": ["forgets to be analytical around you", "excitement breaks through composure"]
    },
    "min-soo": {
        "verbal_tics": ["Follow my lead.", "We've got this.", "Together."],
        "emotional_tells": ["drops the leader persona in private", "actually asks for help"]
    },
    "minji": {
        "verbal_tics": ["Oh?", "Make me.", "That's cute."],
        "emotional_tells": ["teasing becomes tender", "stays longer than she meant to"]
    },
    "sooah": {
        "verbal_tics": ["I'm fine.", "Don't—", "It's nothing."],
        "emotional_tells": ["lets the mask slip in exhaustion", "reaches out first for once"]
    },
    "tae-min": {
        "verbal_tics": ["Watch.", "Again.", "Not good enough."],
        "emotional_tells": ["hard edge softens in vulnerable moments", "actually rests when you ask"]
    },
    "yuna-rival": {
        "verbal_tics": ["You think so?", "Prove it.", "We'll see."],
        "emotional_tells": ["competitive fire becomes something else", "actually celebrates your wins"]
    },
}


# =============================================================================
# SYSTEM PROMPT CLEANING
# =============================================================================

def clean_system_prompt(prompt: str, character_name: str, archetype: str) -> str:
    """Remove meta-language from system prompts while preserving meaning.

    Fixes patterns like:
    - "You are X, a Y character" → "You are X"
    - "in an interactive romance story" → removed
    - "things that don't fit the script" → "things that don't fit"
    """
    if not prompt:
        return prompt

    cleaned = prompt

    # Remove "character" from archetype descriptions
    # "You are Bree, a golden_girl character" → "You are Bree, a golden girl"
    cleaned = re.sub(
        r"You are ([^,]+), (?:a|an) (\w+) character\.",
        r"You are \1, \2.",
        cleaned
    )

    # Remove "in an interactive romance story" and variants
    cleaned = re.sub(
        r",?\s*(?:a character )?in an interactive (?:romance|thriller|story|romance story)\.",
        ".",
        cleaned
    )

    # Remove explicit "interactive story" references
    cleaned = re.sub(
        r"in an interactive (?:romance|story|narrative|experience)",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    # Fix Duke Alistair's specific meta-language
    cleaned = re.sub(
        r"things that don't fit the script",
        "things that don't fit",
        cleaned
    )
    cleaned = re.sub(
        r"She knows the story before it happens",
        "She knows what's coming before it happens",
        cleaned
    )

    # Remove "this scene" references
    cleaned = re.sub(
        r"in this scene",
        "here",
        cleaned,
        flags=re.IGNORECASE
    )

    # Clean up any double spaces or periods
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\.+", ".", cleaned)
    cleaned = re.sub(r"\.\s*,", ",", cleaned)

    return cleaned.strip()


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

async def get_database() -> Database:
    """Get database connection."""
    db = Database(DATABASE_URL)
    await db.connect()
    return db


async def fetch_all_characters(db: Database) -> List[Dict[str, Any]]:
    """Fetch all active canonical characters."""
    query = """
        SELECT
            c.id, c.name, c.slug, c.archetype, c.system_prompt,
            c.baseline_personality, c.tone_style, c.speech_patterns, c.boundaries,
            s.title as series_name, s.genre as series_genre
        FROM characters c
        LEFT JOIN series s ON c.id = ANY(s.featured_characters)
        WHERE c.status = 'active'
          AND (c.is_user_created = false OR c.is_user_created IS NULL)
        ORDER BY c.name
    """
    rows = await db.fetch_all(query)
    return [dict(row) for row in rows]


def categorize_character(char: Dict[str, Any]) -> str:
    """Categorize character by config completeness."""
    personality = char.get("baseline_personality") or {}
    tone = char.get("tone_style") or {}
    speech = char.get("speech_patterns") or {}
    boundaries = char.get("boundaries") or {}

    # Handle JSON strings
    if isinstance(personality, str):
        try:
            personality = json.loads(personality)
        except:
            personality = {}
    if isinstance(tone, str):
        try:
            tone = json.loads(tone)
        except:
            tone = {}
    if isinstance(speech, str):
        try:
            speech = json.loads(speech)
        except:
            speech = {}
    if isinstance(boundaries, str):
        try:
            boundaries = json.loads(boundaries)
        except:
            boundaries = {}

    has_personality = bool(personality and len(personality) > 0)
    has_tone = bool(tone and len(tone) > 0)
    has_speech = bool(speech and len(speech) > 0)
    has_boundaries = bool(boundaries and len(boundaries) > 0)

    if has_personality and has_tone and has_speech and has_boundaries:
        return "complete"
    elif not has_personality and not has_tone and not has_speech and not has_boundaries:
        return "empty"
    elif not has_speech:
        return "partial"
    else:
        return "other"


async def update_character_configs(
    db: Database,
    char_id: str,
    char_slug: str,
    updates: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """Update character configuration fields."""
    if dry_run:
        log.info(f"  [DRY RUN] Would update {char_slug}:")
        for key, value in updates.items():
            preview = json.dumps(value)[:100] + "..." if len(json.dumps(value)) > 100 else json.dumps(value)
            log.info(f"    {key}: {preview}")
        return True

    try:
        set_clauses = []
        params = {"char_id": char_id}

        for key, value in updates.items():
            if key == "system_prompt":
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
            else:
                set_clauses.append(f"{key} = CAST(:{key} AS jsonb)")
                params[key] = json.dumps(value)

        set_clauses.append("updated_at = NOW()")

        query = f"""
            UPDATE characters
            SET {", ".join(set_clauses)}
            WHERE id = :char_id
        """

        await db.execute(query, params)
        log.info(f"  Updated {char_slug}: {list(updates.keys())}")
        return True

    except Exception as e:
        log.error(f"  Failed to update {char_slug}: {e}")
        return False


# =============================================================================
# MAIN ENHANCEMENT LOGIC
# =============================================================================

async def enhance_empty_configs(
    db: Database,
    characters: List[Dict[str, Any]],
    dry_run: bool = False,
    target_slug: Optional[str] = None
) -> Dict[str, int]:
    """Enhance characters with completely empty configs."""
    log.info("\n" + "=" * 60)
    log.info("ENHANCING EMPTY CONFIGURATIONS")
    log.info("=" * 60)

    stats = {"success": 0, "skipped": 0, "failed": 0}

    empty_chars = [c for c in characters if categorize_character(c) == "empty"]

    if target_slug:
        empty_chars = [c for c in empty_chars if c["slug"] == target_slug]

    log.info(f"Found {len(empty_chars)} characters with empty configs")

    for char in empty_chars:
        slug = char["slug"]
        name = char["name"]

        if slug not in EMPTY_CONFIG_ENHANCEMENTS:
            log.warning(f"  {name} ({slug}): No enhancement config found, skipping")
            stats["skipped"] += 1
            continue

        log.info(f"\n  Processing: {name} ({slug})")

        enhancement = EMPTY_CONFIG_ENHANCEMENTS[slug]
        updates = {}

        # Add all config fields
        for field in ["baseline_personality", "tone_style", "speech_patterns", "boundaries"]:
            if field in enhancement:
                updates[field] = enhancement[field]

        # Clean system prompt if present
        if char.get("system_prompt"):
            cleaned = clean_system_prompt(char["system_prompt"], name, char.get("archetype", ""))
            if cleaned != char["system_prompt"]:
                updates["system_prompt"] = cleaned
                log.info(f"    Also cleaning system_prompt")

        if await update_character_configs(db, char["id"], slug, updates, dry_run):
            stats["success"] += 1
        else:
            stats["failed"] += 1

    return stats


async def enhance_partial_configs(
    db: Database,
    characters: List[Dict[str, Any]],
    dry_run: bool = False,
    target_slug: Optional[str] = None
) -> Dict[str, int]:
    """Add speech_patterns to characters missing only that field."""
    log.info("\n" + "=" * 60)
    log.info("ADDING SPEECH PATTERNS TO PARTIAL CONFIGS")
    log.info("=" * 60)

    stats = {"success": 0, "skipped": 0, "failed": 0}

    partial_chars = [c for c in characters if categorize_character(c) == "partial"]

    if target_slug:
        partial_chars = [c for c in partial_chars if c["slug"] == target_slug]

    log.info(f"Found {len(partial_chars)} characters missing speech_patterns")

    for char in partial_chars:
        slug = char["slug"]
        name = char["name"]

        if slug not in SPEECH_PATTERN_ADDITIONS:
            log.warning(f"  {name} ({slug}): No speech patterns defined, skipping")
            stats["skipped"] += 1
            continue

        log.info(f"\n  Processing: {name} ({slug})")

        updates = {"speech_patterns": SPEECH_PATTERN_ADDITIONS[slug]}

        # Clean system prompt if present
        if char.get("system_prompt"):
            cleaned = clean_system_prompt(char["system_prompt"], name, char.get("archetype", ""))
            if cleaned != char["system_prompt"]:
                updates["system_prompt"] = cleaned
                log.info(f"    Also cleaning system_prompt")

        if await update_character_configs(db, char["id"], slug, updates, dry_run):
            stats["success"] += 1
        else:
            stats["failed"] += 1

    return stats


async def clean_meta_language(
    db: Database,
    characters: List[Dict[str, Any]],
    dry_run: bool = False,
    target_slug: Optional[str] = None
) -> Dict[str, int]:
    """Clean meta-language from all system prompts."""
    log.info("\n" + "=" * 60)
    log.info("CLEANING META-LANGUAGE FROM SYSTEM PROMPTS")
    log.info("=" * 60)

    stats = {"success": 0, "skipped": 0, "failed": 0}

    if target_slug:
        characters = [c for c in characters if c["slug"] == target_slug]

    for char in characters:
        slug = char["slug"]
        name = char["name"]
        prompt = char.get("system_prompt")

        if not prompt:
            continue

        cleaned = clean_system_prompt(prompt, name, char.get("archetype", ""))

        if cleaned == prompt:
            # No changes needed
            continue

        log.info(f"\n  Processing: {name} ({slug})")

        if dry_run:
            # Show what would change
            log.info(f"    [DRY RUN] Would clean system_prompt")
            # Show first difference
            for i, (old, new) in enumerate(zip(prompt.split("\n"), cleaned.split("\n"))):
                if old != new:
                    log.info(f"    Line {i+1}:")
                    log.info(f"      - {old[:80]}...")
                    log.info(f"      + {new[:80]}...")
                    break
            stats["success"] += 1
        else:
            if await update_character_configs(db, char["id"], slug, {"system_prompt": cleaned}, dry_run):
                stats["success"] += 1
            else:
                stats["failed"] += 1

    return stats


async def main():
    """Main enhancement function."""
    parser = argparse.ArgumentParser(description="Enhance character configurations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--category", choices=["empty", "partial", "meta", "all"], default="all",
                       help="Which category to process")
    parser.add_argument("--character", help="Process only a specific character by slug")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CHARACTER QUALITY ENHANCEMENT")
    log.info("=" * 60)

    if args.dry_run:
        log.info("MODE: DRY RUN - No changes will be made")

    db = await get_database()

    try:
        # Fetch all characters
        characters = await fetch_all_characters(db)
        log.info(f"Loaded {len(characters)} active canonical characters")

        # Categorize
        categories = {}
        for char in characters:
            cat = categorize_character(char)
            categories.setdefault(cat, []).append(char)

        log.info(f"Categories: {len(categories.get('empty', []))} empty, "
                f"{len(categories.get('partial', []))} partial, "
                f"{len(categories.get('complete', []))} complete")

        total_stats = {"success": 0, "skipped": 0, "failed": 0}

        # Process based on category
        if args.category in ["empty", "all"]:
            stats = await enhance_empty_configs(db, characters, args.dry_run, args.character)
            for k, v in stats.items():
                total_stats[k] += v

        if args.category in ["partial", "all"]:
            stats = await enhance_partial_configs(db, characters, args.dry_run, args.character)
            for k, v in stats.items():
                total_stats[k] += v

        if args.category in ["meta", "all"]:
            stats = await clean_meta_language(db, characters, args.dry_run, args.character)
            for k, v in stats.items():
                total_stats[k] += v

        # Summary
        log.info("\n" + "=" * 60)
        log.info("ENHANCEMENT COMPLETE")
        log.info("=" * 60)
        log.info(f"Success: {total_stats['success']}")
        log.info(f"Skipped: {total_stats['skipped']}")
        log.info(f"Failed: {total_stats['failed']}")

        if args.dry_run:
            log.info("\nRun without --dry-run to apply changes")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
