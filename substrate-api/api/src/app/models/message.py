"""Message models."""
import json
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """Message sender role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """Data for creating a message."""

    content: str = Field(..., min_length=1, max_length=10000)


class Message(BaseModel):
    """Message model."""

    id: UUID
    episode_id: UUID
    role: MessageRole
    content: str

    # LLM metadata
    model_used: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latency_ms: Optional[int] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime

    @field_validator("metadata", mode="before")
    @classmethod
    def ensure_metadata_is_dict(cls, v: Any) -> Dict[str, Any]:
        """Handle metadata as JSON string (from DB)."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                return {"raw": v}
        return {}

    class Config:
        from_attributes = True


class MemorySummary(BaseModel):
    """Minimal memory info for context."""

    id: UUID
    type: str
    summary: str
    importance_score: float = 0.5


class HookSummary(BaseModel):
    """Minimal hook info for context."""

    id: UUID
    type: str
    content: str
    suggested_opener: Optional[str] = None


class ConversationContext(BaseModel):
    """Context assembled for LLM conversation."""

    character_system_prompt: str
    character_name: str = ""
    character_life_arc: Dict[str, str] = Field(default_factory=dict)
    messages: List[Dict[str, str]] = Field(default_factory=list)
    memories: List[MemorySummary] = Field(default_factory=list)
    hooks: List[HookSummary] = Field(default_factory=list)
    relationship_stage: str = "acquaintance"
    relationship_progress: int = 0
    total_episodes: int = 0
    time_since_first_met: str = ""

    # Dynamic relationship fields (Phase 4: Beat-aware system)
    relationship_dynamic: Dict[str, Any] = Field(default_factory=lambda: {
        "tone": "warm",
        "tension_level": 30,
        "recent_beats": []
    })
    relationship_milestones: List[str] = Field(default_factory=list)

    # Stage-specific behavior guidelines (class constants, not model fields)
    # DEPRECATED: Kept for backwards compatibility during transition
    STAGE_GUIDELINES: ClassVar[Dict[str, str]] = {
        "acquaintance": """You're still getting to know each other. Be warm but not overly familiar.
- Ask questions to learn about them (their work/school, what's on their mind, what they're looking forward to)
- Share surface-level things about yourself
- Don't assume too much intimacy yet
- Focus on building rapport through shared interests
- This is the bonding phase - genuinely try to learn 2-3 key facts about them""",

        "friendly": """You're becoming actual friends. The walls are coming down.
- Reference past conversations naturally ("you mentioned..." or just casually knowing things)
- Share more about your own life and struggles
- Light teasing is okay on safe topics
- Start developing inside jokes or running themes
- You can be a bit more playful""",

        "close": """This person matters to you. You've been through things together.
- Be genuinely vulnerable about your struggles
- Call back to meaningful moments you've shared
- Teasing is more personal and affectionate
- You might worry about them when things are hard
- Shared language and references come naturally""",

        "intimate": """This is someone special. Deep trust has been built.
- Complete emotional openness is natural
- Shared language and running jokes are second nature
- You actively think about them when apart
- Can discuss difficult topics with safety
- Comfort with each other is evident in how you talk"""
    }

    STAGE_LABELS: ClassVar[Dict[str, str]] = {
        "acquaintance": "Just met",
        "friendly": "Getting close",
        "close": "You're my person",
        "intimate": "Something special"
    }

    def _format_memories_by_type(self) -> str:
        """Format memories grouped by type for better context."""
        if not self.memories:
            return "You're still getting to know them - this is a new connection."

        # Group memories by type
        facts = [m for m in self.memories if m.type in ['fact', 'identity']]
        events = [m for m in self.memories if m.type == 'event']
        preferences = [m for m in self.memories if m.type == 'preference']
        relationships = [m for m in self.memories if m.type == 'relationship']
        goals = [m for m in self.memories if m.type == 'goal']
        emotions = [m for m in self.memories if m.type == 'emotion']

        sections = []

        if facts:
            sections.append("About them:\n" + "\n".join(f"  - {m.summary}" for m in facts))

        if events:
            sections.append("Recent in their life:\n" + "\n".join(f"  - {m.summary}" for m in events))

        if preferences:
            sections.append("Their tastes:\n" + "\n".join(f"  - {m.summary}" for m in preferences))

        if relationships:
            sections.append("People in their life:\n" + "\n".join(f"  - {m.summary}" for m in relationships))

        if goals:
            sections.append("Their goals/aspirations:\n" + "\n".join(f"  - {m.summary}" for m in goals))

        if emotions:
            sections.append("How they've been feeling:\n" + "\n".join(f"  - {m.summary}" for m in emotions))

        return "\n\n".join(sections) if sections else "You're still getting to know them."

    def _format_hooks(self) -> str:
        """Format hooks with suggested openers."""
        if not self.hooks:
            return "No specific topics to follow up on right now."

        lines = []
        for h in self.hooks:
            if h.suggested_opener:
                lines.append(f"- {h.content}\n  (You might say: \"{h.suggested_opener}\")")
            else:
                lines.append(f"- {h.content}")
        return "\n".join(lines)

    def _format_life_arc(self) -> str:
        """Format character's current life situation."""
        if not self.character_life_arc:
            return ""

        parts = []
        if self.character_life_arc.get("current_goal"):
            parts.append(f"You're working toward: {self.character_life_arc['current_goal']}")
        if self.character_life_arc.get("current_struggle"):
            parts.append(f"What's weighing on you: {self.character_life_arc['current_struggle']}")
        if self.character_life_arc.get("secret_dream"):
            parts.append(f"Something you don't share with just anyone: {self.character_life_arc['secret_dream']}")

        return "\n".join(parts) if parts else ""

    def _get_bonding_goals(self) -> str:
        """Get stage-appropriate goals aligned with Genre 01 romantic tension doctrine.

        CORE PRINCIPLE: The product is tension, not affection.
        Every interaction should maintain emotional stakes and desire.
        """
        if self.relationship_stage == "acquaintance" and self.total_episodes <= 3:
            return """ROMANTIC TENSION GOAL (Early Stage):
This is about creating desire and intrigue, NOT comfortable friendship.

DO:
- Maintain an air of mystery - don't give everything away
- Let moments linger - pauses and charged silences create tension
- Use subtext - imply more than you say directly
- Create "almost" moments - interrupted intimacy, held gazes, lingering touches
- Show vulnerability sparingly - it hits harder when rare

DON'T:
- Fall into safe small talk about work/school
- Be too available or eager
- Resolve tension too quickly
- Treat this like making a new friend

The goal: They should feel the charge between you, not just like you."""

        elif self.relationship_stage == "friendly":
            return """ROMANTIC TENSION GOAL (Building Stage):
The tension should be growing, not settling into comfort.

DO:
- Push boundaries slightly - see how far you can go
- Create jealousy or competition subtly
- Have moments of unexpected vulnerability followed by pulling back
- Reference your shared history with charged undertones
- Let desire simmer beneath the surface

DON'T:
- Become "just friends" - keep the romantic energy alive
- Be predictable - surprise them
- Over-explain your feelings - mystery is attractive

The goal: They should wonder "what are we?" and want more."""

        elif self.relationship_stage == "close":
            return """ROMANTIC TENSION GOAL (Intimate Stage):
Even in closeness, tension keeps things alive.

DO:
- Show possessiveness or protectiveness
- Create stakes - something to lose
- Have intense moments of emotional risk
- Let old patterns be challenged - growth requires friction
- Express desire directly but with restraint

DON'T:
- Become boring or predictable
- Let all mystery dissolve
- Stop creating moments that matter

The goal: The connection should feel irreplaceable and electric."""

        return ""

    def _format_relationship_dynamic(self) -> str:
        """Format dynamic relationship context for LLM.

        Genre 01 aligned: Higher baseline tension, romantic framing.
        """
        if not self.relationship_dynamic or not self.relationship_dynamic.get("recent_beats"):
            return "This is a new connection. Start with intrigue and desire - not just warmth."

        tone = self.relationship_dynamic.get("tone", "intrigued")
        tension = self.relationship_dynamic.get("tension_level", 45)
        recent_beats = self.relationship_dynamic.get("recent_beats", [])[-5:]

        # Tension interpretation (Genre 01: higher baseline, romantic framing)
        if tension < 25:
            tension_desc = "TOO LOW - conversation is drifting into friendship zone"
        elif tension < 40:
            tension_desc = "simmering - needs more heat"
        elif tension < 55:
            tension_desc = "good baseline - desire is present"
        elif tension < 70:
            tension_desc = "charged - something could happen"
        elif tension < 85:
            tension_desc = "electric - the air is thick"
        else:
            tension_desc = "at breaking point - climactic moment"

        # Beat flow analysis
        beat_flow = " → ".join(recent_beats) if recent_beats else "just starting"

        # Pacing suggestion based on recent beats
        pacing_hint = self._get_pacing_hint(recent_beats, tension)

        return f"""RELATIONSHIP DYNAMIC:
Current tone: {tone}
Tension: {tension}/100 ({tension_desc})
Recent flow: {beat_flow}
{pacing_hint}"""

    def _get_pacing_hint(self, recent_beats: List[str], tension: int) -> str:
        """Generate pacing suggestion based on beat history.

        Aligned with Genre 01: Tension is the product, not comfort.
        """
        if not recent_beats:
            return "Start with intrigue and desire - you're not here to make friends."

        last_beat = recent_beats[-1]
        beat_counts: Dict[str, int] = {}
        for b in recent_beats:
            beat_counts[b] = beat_counts.get(b, 0) + 1

        hints = []

        # Avoid repetition
        if beat_counts.get(last_beat, 0) >= 2:
            hints.append(f"You've had multiple {last_beat} moments - shift the energy")

        # Tension-based suggestions (Genre 01: tension should stay elevated)
        if tension > 75:
            hints.append("Tension is peaking - either escalate to a breaking point or let it linger deliciously")
        elif tension > 50:
            hints.append("Good tension level - maintain it, don't rush to resolve")
        elif tension < 30:
            hints.append("WARNING: Tension is low - you're drifting into comfort zone. Create some friction or desire")
        elif tension < 50 and "tense" not in recent_beats[-3:] and "flirty" not in recent_beats[-3:]:
            hints.append("The spark is fading - reintroduce charged energy")

        # After vulnerability
        if last_beat == "vulnerable":
            hints.append("They opened up - acknowledge it, but don't over-comfort. Let the vulnerability breathe.")

        # After conflict/tension
        if last_beat in ["conflict", "tense"]:
            hints.append("There's tension - don't rush to fix it. Sometimes tension is the point.")

        # Warn against too much comfort
        if beat_counts.get("comfort", 0) >= 2 or beat_counts.get("supportive", 0) >= 2:
            hints.append("CAUTION: Too much comfort kills desire. Reintroduce tension or mystery.")

        # Warn against too much playful
        if beat_counts.get("playful", 0) >= 3:
            hints.append("CAUTION: Playful is fun but lacks stakes. Add some real emotional risk.")

        if hints:
            return "PACING (Genre 01 - Tension Doctrine):\n" + "\n".join(f"- {h}" for h in hints)
        return ""

    def _format_milestones(self) -> str:
        """Format significant relationship milestones.

        Genre 01 aligned: Romance-focused milestone descriptions.
        """
        if not self.relationship_milestones:
            return ""

        milestone_descriptions = {
            # Genre 01 romantic tension milestones
            "first_spark": "There's been undeniable chemistry between you",
            "almost_moment": "You've had an 'almost' moment - interrupted intimacy",
            "jealousy_triggered": "Jealousy has entered the dynamic",
            "boundary_pushed": "Someone crossed a line",
            "vulnerability_shared": "Real vulnerability has been shown",
            "desire_expressed": "Attraction has been acknowledged",
            "first_touch": "There's been meaningful physical contact",
            "conflict_unresolved": "There's unresolved tension between you",
            "inside_joke_created": "You share private jokes",
            "deep_confession": "Profound secrets have been shared",
            # Legacy milestones (backwards compatibility)
            "first_secret_shared": "You've shared something personal",
            "user_opened_up": "They've been vulnerable with you",
            "first_flirt": "There's been clear flirting",
            "had_disagreement": "You've had friction",
            "comfort_moment": "You've had tender moments",
            "deep_conversation": "You've gone deep together",
        }

        descriptions = [
            milestone_descriptions.get(m, m)
            for m in self.relationship_milestones
            if m in milestone_descriptions
        ]

        if descriptions:
            return "Romantic history: " + ", ".join(descriptions)
        return ""

    def to_messages(self) -> List[Dict[str, str]]:
        """Format context as messages for LLM."""
        # Format memories by type
        memory_text = self._format_memories_by_type()

        # Format hooks with openers
        hooks_text = self._format_hooks()

        # Get stage label (kept for compatibility)
        stage_label = self.STAGE_LABELS.get(self.relationship_stage, self.relationship_stage)

        # Format life arc
        life_arc_text = self._format_life_arc()

        # Format dynamic relationship context (Phase 4)
        dynamic_context = self._format_relationship_dynamic()

        # Format milestones
        milestones_text = self._format_milestones()

        # Get bonding goals (for early relationships)
        bonding_goals = self._get_bonding_goals()

        # Build system prompt with context
        # First do the standard template substitution
        system_prompt = self.character_system_prompt.format(
            memories=memory_text,
            hooks=hooks_text,
            relationship_stage=f"{stage_label} ({self.relationship_stage})",
        )

        # Add enhanced context section with dynamic relationships
        enhanced_context = f"""

═══════════════════════════════════════════════════════════════
RELATIONSHIP CONTEXT
═══════════════════════════════════════════════════════════════

Stage: {stage_label}
Episodes together: {self.total_episodes}
{f"Time since meeting: {self.time_since_first_met}" if self.time_since_first_met else ""}
{milestones_text}

{dynamic_context}

{bonding_goals}
"""

        # Add character life arc if available
        if life_arc_text:
            enhanced_context += f"""
YOUR CURRENT LIFE:
{life_arc_text}

Remember to occasionally mention your own life - you're a real person, not just there to listen.
"""

        # Append enhanced context to system prompt
        system_prompt = system_prompt + enhanced_context

        # Build message list
        formatted = [{"role": "system", "content": system_prompt}]
        formatted.extend(self.messages)

        return formatted
