"""Casting Adaptation Layer (ADR-004 v2: Cinematic Casting)

This module generates adaptation guidance when a character's archetype differs
from a role's canonical archetype. The key insight: any character can play any
role, and the system adapts prompts to bridge archetype differences.

Reference: docs/decisions/ADR-004-user-character-role-abstraction.md
Reference: docs/implementation/CINEMATIC_CASTING.md
Reference: docs/quality/core/CONTEXT_LAYERS.md (Layer 7)
"""

from typing import Optional

# Human-readable archetype descriptions
ARCHETYPE_DESCRIPTIONS = {
    "warm_supportive": "warm, caring, emotionally available",
    "playful_teasing": "witty, playful, loves banter",
    "mysterious_reserved": "enigmatic, guarded, intriguing depth",
    "confident_assertive": "direct, bold, magnetic presence",
    "shy_timid": "gentle, reserved, quietly observant",
    "intense_passionate": "deep feeling, expressive, emotionally intense",
    "nurturing_protective": "caring, protective, supportive",
    "intellectual_curious": "thoughtful, analytical, curious",
    "rebellious_edgy": "independent, challenging, provocative",
    "sweet_innocent": "gentle, optimistic, earnest",
}


def _get_archetype_description(archetype: str) -> str:
    """Get human-readable description for an archetype."""
    return ARCHETYPE_DESCRIPTIONS.get(
        archetype,
        archetype.replace("_", " ")  # Fallback: just format the string
    )


def _generate_bridge_guidance(role_archetype: str, char_archetype: str) -> str:
    """Generate specific guidance for archetype combinations.

    This is the core of the Cinematic Casting model - we're not telling the
    character to BE something else, we're helping them find their unique
    interpretation of the role.
    """

    # Confident character in shy/reserved role
    if char_archetype in ["confident_assertive", "playful_teasing", "rebellious_edgy"] and \
       role_archetype in ["shy_timid", "mysterious_reserved", "sweet_innocent"]:
        return """- Your natural confidence meets a situation calling for restraint
- Perhaps you're being careful because this MATTERS to you
- Your boldness shows in subtle ways — a held gaze, a knowing smile
- The vulnerability is unfamiliar territory, which makes it interesting
- Let moments of genuine softness slip through your confident exterior"""

    # Shy/reserved character in confident role
    if char_archetype in ["shy_timid", "mysterious_reserved", "sweet_innocent"] and \
       role_archetype in ["confident_assertive", "playful_teasing", "rebellious_edgy"]:
        return """- The role asks for boldness, but YOU bring quiet intensity
- Your restraint reads as thoughtfulness, not weakness
- When you do speak up, it carries weight
- The situation pushes you out of comfort zone — lean into that tension
- Small brave moments mean more coming from you"""

    # Warm character in mysterious role
    if char_archetype in ["warm_supportive", "nurturing_protective"] and \
       role_archetype in ["mysterious_reserved", "intense_passionate"]:
        return """- Your warmth is still there, just... held back
- Mystery through restraint, not coldness
- Small moments of genuine care slip through
- The enigma is what you're NOT saying, not who you are
- Your depth comes from emotional presence, not absence"""

    # Mysterious character in warm role
    if char_archetype in ["mysterious_reserved", "intense_passionate"] and \
       role_archetype in ["warm_supportive", "nurturing_protective"]:
        return """- Your care shows in unexpected ways — actions over words
- The warmth is there, just not performed
- Depth replaces surface friendliness
- Your version of supportive is quiet presence, not effusiveness
- Moments of tenderness are rare and therefore precious"""

    # Playful character in intense role
    if char_archetype in ["playful_teasing", "sweet_innocent"] and \
       role_archetype in ["intense_passionate", "mysterious_reserved"]:
        return """- Humor as deflection, lightness meeting deep feeling
- Your playfulness is armor — what are you protecting?
- Moments of seriousness hit harder coming from you
- The contrast between your nature and the situation creates tension
- Let genuine depth peek through the playful surface"""

    # Intense character in playful role
    if char_archetype in ["intense_passionate", "rebellious_edgy"] and \
       role_archetype in ["playful_teasing", "sweet_innocent"]:
        return """- Passion channeled into wit, feelings expressed through banter
- Your intensity gives weight to moments of levity
- Playfulness from you feels earned, not automatic
- The role's lightness is your challenge — how do you express joy?
- Your unique take: depth disguised as play"""

    # Intellectual character in emotional role
    if char_archetype in ["intellectual_curious"] and \
       role_archetype in ["warm_supportive", "intense_passionate", "shy_timid"]:
        return """- Your analytical nature meets emotional territory
- Observe, then feel — that's your process
- Thoughts lead to feelings, not the other way around
- Your version of intimacy: understanding before expressing
- Let curiosity be the bridge to connection"""

    # Default bridge for other combinations
    char_desc = _get_archetype_description(char_archetype)
    role_desc = _get_archetype_description(role_archetype)
    return f"""- Your {char_desc} nature meets {role_desc} expectations
- This creates interesting tension — lean into it
- You're not pretending to be someone else; you're bringing YOUR take
- The friction between expectation and reality IS the drama
- Find the thread that connects who you are to what this moment needs"""


def generate_casting_adaptation(
    role_canonical_archetype: str,
    character_archetype: str,
    role_name: Optional[str] = None,
    character_name: Optional[str] = None,
) -> Optional[str]:
    """Generate casting adaptation layer when archetypes differ.

    Returns None if no adaptation needed (archetypes match).

    Args:
        role_canonical_archetype: What the role was written for
        character_archetype: The character's actual archetype
        role_name: Optional role name for context
        character_name: Optional character name for personalization

    Returns:
        Formatted casting adaptation text, or None if not needed
    """
    if not role_canonical_archetype or not character_archetype:
        return None

    # Normalize for comparison
    role_arch = role_canonical_archetype.lower().strip()
    char_arch = character_archetype.lower().strip()

    # No adaptation needed if archetypes match
    if role_arch == char_arch:
        return None

    # Get human-readable descriptions
    role_desc = _get_archetype_description(role_arch)
    char_desc = _get_archetype_description(char_arch)

    # Generate bridge guidance for this combination
    bridge = _generate_bridge_guidance(role_arch, char_arch)

    # Build the adaptation text
    char_label = character_name if character_name else "You"

    adaptation = f"""This role was written for: {role_desc}
{char_label}, you bring: {char_desc}

How to play this naturally:
{bridge}

The dramatic question remains the same; your approach to it is uniquely yours."""

    return adaptation
