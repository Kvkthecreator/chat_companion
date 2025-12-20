"""Director Service - Semantic evaluation and runtime orchestration.

The Director is the system entity that observes, evaluates, and orchestrates
episode progression through semantic understanding rather than state machines.

Director Protocol v2.0:
- PRE-GUIDANCE: Pacing, tension, physical anchors BEFORE character responds
- POST-EVALUATION: Visual detection, completion status AFTER response

Reference: docs/quality/core/DIRECTOR_PROTOCOL.md
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.episode_template import EpisodeTemplate, AutoSceneMode
from app.models.session import Session
from app.models.evaluation import (
    EvaluationType,
    FlirtArchetype,
    FLIRT_ARCHETYPES,
    generate_share_id,
)
from app.services.llm import LLMService

log = logging.getLogger(__name__)


# Genre-specific tension patterns for pre-guidance
GENRE_BEATS = {
    "romantic_tension": {
        "establish": "set the scene, create first spark of attraction",
        "develop": "build rapport through vulnerability, test boundaries",
        "escalate": "unspoken tension rises, proximity matters more",
        "peak": "the moment before something changes forever",
        "resolve": "land the emotional payoff or create the hook for next time",
    },
    "psychological_thriller": {
        "establish": "something feels off, trust is uncertain",
        "develop": "information drip, questions multiply",
        "escalate": "stakes become personal, escape narrows",
        "peak": "truth or consequences, no safe exit",
        "resolve": "revelation or cliffhanger, nothing is the same",
    },
    "slice_of_life": {
        "establish": "comfortable presence, small details matter",
        "develop": "shared moments build connection",
        "escalate": "depth emerges from simplicity",
        "peak": "quiet intimacy, being truly known",
        "resolve": "warmth lingers, anticipation for next time",
    },
}


@dataclass
class DirectorGuidance:
    """Pre-response guidance for character LLM.

    This is injected into context BEFORE the character generates a response.
    It influences pacing, tension, and genre-appropriate behavior.
    """
    pacing: str = "develop"  # establish/develop/escalate/peak/resolve
    tension_note: Optional[str] = None  # Subtle direction for the actor
    physical_anchor: Optional[str] = None  # Sensory reminder
    genre_beat: Optional[str] = None  # Genre-specific guidance

    def to_prompt_section(self) -> str:
        """Format as prompt section for character LLM."""
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "DIRECTOR NOTE (internal guidance - do not mention explicitly)",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"Pacing: {self.pacing.upper()}",
        ]

        if self.tension_note:
            lines.append(f"Tension: {self.tension_note}")

        if self.physical_anchor:
            lines.append(f"Ground in: {self.physical_anchor}")

        if self.genre_beat:
            lines.append(f"Beat: {self.genre_beat}")

        lines.append("")
        lines.append("Let this guide your response naturally. Don't force it.")

        return "\n".join(lines)


@dataclass
class DirectorActions:
    """Deterministic outputs for system behavior.

    These are explicit actions the system should take - no interpretation needed.
    """
    visual_type: str = "none"  # character/object/atmosphere/instruction/none
    visual_hint: Optional[str] = None  # What to show (for image generation)
    suggest_next: bool = False  # Suggest moving to next episode
    deduct_sparks: int = 0  # Sparks to deduct for scene generation
    save_memory: bool = False  # Save evaluation as memory
    memory_content: Optional[str] = None  # Content to save
    needs_sparks: bool = False  # User needs more sparks (first-time prompt)


@dataclass
class DirectorOutput:
    """Output from Director processing."""
    # Core state
    turn_count: int
    is_complete: bool
    completion_trigger: Optional[str]  # "semantic", "turn_limit", None

    # Semantic evaluation result
    evaluation: Optional[Dict[str, Any]] = None

    # Deterministic actions
    actions: Optional[DirectorActions] = None

    # Legacy compatibility (will be removed)
    extracted_memories: List[Dict[str, Any]] = field(default_factory=list)
    beat_data: Optional[Dict[str, Any]] = None
    extracted_hooks: List[Dict[str, Any]] = field(default_factory=list)
    structured_response: Optional[Dict[str, Any]] = None


class DirectorService:
    """Director service - semantic evaluation and runtime orchestration.

    Director Protocol v2.0 - Two-Phase Model:

    PHASE 1: PRE-GUIDANCE (before character LLM)
    - Determines pacing based on turn count and episode budget
    - Generates tension notes based on recent exchange
    - Provides physical anchors from situation
    - Adds genre-appropriate beat guidance

    PHASE 2: POST-EVALUATION (after character LLM)
    - Detects visual moments (character/object/atmosphere/instruction)
    - Determines episode completion status
    - Triggers memory extraction and hooks

    The Director is the "brain, eyes, ears, and hands" of the conversation system:
    - Eyes/Ears: Observes all exchanges
    - Brain: Evaluates semantically (not state machines)
    - Hands: Triggers deterministic actions
    """

    def __init__(self, db):
        self.db = db
        self.llm = LLMService.get_instance()

    # =========================================================================
    # PHASE 1: PRE-GUIDANCE (before character response)
    # =========================================================================

    def determine_pacing(
        self,
        turn_count: int,
        turn_budget: Optional[int],
    ) -> str:
        """Determine pacing phase based on turn position.

        Returns: establish/develop/escalate/peak/resolve
        """
        if turn_budget and turn_budget > 0:
            # Bounded episode: use position in arc
            position = turn_count / turn_budget
            if position < 0.15:
                return "establish"
            elif position < 0.4:
                return "develop"
            elif position < 0.7:
                return "escalate"
            elif position < 0.9:
                return "peak"
            else:
                return "resolve"
        else:
            # Open episode: use turn count heuristics
            if turn_count < 2:
                return "establish"
            elif turn_count < 5:
                return "develop"
            elif turn_count < 10:
                return "escalate"
            elif turn_count < 15:
                return "peak"
            else:
                return "resolve"

    async def generate_pre_guidance(
        self,
        messages: List[Dict[str, str]],
        genre: str,
        situation: str,
        dramatic_question: str,
        turn_count: int,
        turn_budget: Optional[int] = None,
    ) -> DirectorGuidance:
        """Generate pre-response guidance for character LLM.

        This is a lightweight LLM call that provides:
        - Pacing phase (algorithmic)
        - Tension note (LLM-generated, contextual)
        - Physical anchor (from situation)
        - Genre beat (from GENRE_BEATS lookup)
        """
        # 1. Determine pacing algorithmically
        pacing = self.determine_pacing(turn_count, turn_budget)

        # 2. Get genre beat from lookup
        genre_key = genre.lower().replace(" ", "_").replace("-", "_")
        genre_beats = GENRE_BEATS.get(genre_key, GENRE_BEATS.get("romantic_tension", {}))
        genre_beat = f"{genre_key}: {genre_beats.get(pacing, 'stay in the moment')}"

        # 3. Extract physical anchor from situation (first sensory phrase)
        physical_anchor = None
        if situation:
            # Take first meaningful chunk for grounding
            physical_anchor = situation.split(".")[0].strip()[:100]

        # 4. Generate tension note via lightweight LLM call
        tension_note = await self._generate_tension_note(
            messages=messages,
            genre=genre,
            dramatic_question=dramatic_question,
            pacing=pacing,
        )

        return DirectorGuidance(
            pacing=pacing,
            tension_note=tension_note,
            physical_anchor=physical_anchor,
            genre_beat=genre_beat,
        )

    async def _generate_tension_note(
        self,
        messages: List[Dict[str, str]],
        genre: str,
        dramatic_question: str,
        pacing: str,
    ) -> Optional[str]:
        """Generate a contextual tension note for the character.

        This is a very short, focused LLM call (~50 tokens output).
        """
        # Only use last 2 exchanges for speed
        recent = messages[-4:] if len(messages) > 4 else messages
        formatted = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in recent
        )

        prompt = f"""You are a director giving a one-line note to an actor in a {genre} scene.

RECENT EXCHANGE:
{formatted}

DRAMATIC TENSION: {dramatic_question}
CURRENT PACING: {pacing}

Give ONE short direction (max 15 words) that helps the actor understand what to lean into for their next line. Focus on subtext, not action.

Examples:
- "She wants to stay but can't admit it—let the pause speak"
- "He's testing you—match his energy but keep something back"
- "The silence is louder than words right now"

Your direction:"""

        try:
            response = await self.llm.generate(
                [{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7,
            )
            # Clean up response
            note = response.content.strip().strip('"').strip("'")
            return note[:150] if note else None
        except Exception as e:
            log.warning(f"Tension note generation failed: {e}")
            return None

    # =========================================================================
    # PHASE 2: POST-EVALUATION (after character response)
    # =========================================================================

    async def evaluate_exchange(
        self,
        messages: List[Dict[str, str]],
        character_name: str,
        genre: str,
        situation: str,
        dramatic_question: str,
    ) -> Dict[str, Any]:
        """Semantic evaluation of exchange.

        Uses LLM to understand the meaning and emotional state of the conversation,
        then extracts minimal structured signals for deterministic action.
        """
        # Format recent messages (last 3 exchanges = 6 messages)
        recent = messages[-6:] if len(messages) > 6 else messages
        formatted = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in recent
        )

        prompt = f"""You are the Director observing a {genre} story.

Character: {character_name}
Situation: {situation}
Core tension: {dramatic_question}

RECENT EXCHANGE:
{formatted}

As a director, observe this moment. Answer naturally, then provide signals.

1. VISUAL: Would this exchange benefit from a visual element?
   - CHARACTER: A shot featuring the character (portrait, expression, pose)
   - OBJECT: Close-up of an item (letter, phone, key, evidence)
   - ATMOSPHERE: Setting/mood without character visible
   - INSTRUCTION: Game-like information (codes, hints, choices)
   - NONE: No visual needed

   If not NONE, describe what should be shown in one evocative sentence.

2. STATUS: Is this episode ready to close, approaching closure, or still unfolding?
   Explain briefly in terms that make sense for this {genre} story.

End with a signal line for parsing:
SIGNAL: [visual: character/object/atmosphere/instruction/none] [status: going/closing/done]
If visual is not "none", add: [hint: <description>]"""

        try:
            response = await self.llm.generate([
                {"role": "system", "content": "You are a story director. Be concise."},
                {"role": "user", "content": prompt}
            ], max_tokens=250)

            return self._parse_evaluation(response.content)
        except Exception as e:
            log.error(f"Director evaluation failed: {e}")
            return {
                "raw_response": "",
                "visual_type": "none",
                "visual_hint": None,
                "status": "going",
            }

    def _parse_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse natural language evaluation into actionable signals."""
        # Extract signal line with visual type
        signal_match = re.search(
            r'SIGNAL:\s*\[visual:\s*(character|object|atmosphere|instruction|none)\]\s*\[status:\s*(going|closing|done)\]',
            response, re.IGNORECASE
        )

        # Extract hint if present
        hint_match = re.search(r'\[hint:\s*([^\]]+)\]', response, re.IGNORECASE)

        if signal_match:
            visual_type = signal_match.group(1).lower()
            status_signal = signal_match.group(2).lower()
            visual_hint = hint_match.group(1).strip() if hint_match else None
        else:
            # Fallback parsing
            visual_type = 'none'
            status_signal = 'done' if 'done' in response.lower() else 'going'
            visual_hint = None

        return {
            "raw_response": response,
            "visual_type": visual_type,
            "visual_hint": visual_hint,
            "status": status_signal,
        }

    def decide_actions(
        self,
        evaluation: Dict[str, Any],
        episode: Optional[EpisodeTemplate],
        session: Session,
    ) -> DirectorActions:
        """Convert semantic evaluation into deterministic actions."""
        actions = DirectorActions()
        turn = session.turn_count + 1  # New turn count after this exchange
        visual_type = evaluation.get("visual_type", "none")

        if not episode:
            return actions

        # --- Visual Generation ---
        auto_mode = getattr(episode, 'auto_scene_mode', AutoSceneMode.OFF)

        if auto_mode == AutoSceneMode.PEAKS:
            # Generate on visual moments (any type except none)
            if visual_type != "none":
                actions.visual_type = visual_type
                actions.visual_hint = evaluation.get("visual_hint")
                # Only charge sparks for image generation (not instruction cards)
                if visual_type in ("character", "object", "atmosphere"):
                    actions.deduct_sparks = getattr(episode, 'spark_cost_per_scene', 5)

        elif auto_mode == AutoSceneMode.RHYTHMIC:
            interval = getattr(episode, 'scene_interval', 3) or 3
            if turn > 0 and turn % interval == 0:
                # Use detected type, or default to character
                actions.visual_type = visual_type if visual_type != "none" else "character"
                actions.visual_hint = evaluation.get("visual_hint") or "the current moment"
                if actions.visual_type in ("character", "object", "atmosphere"):
                    actions.deduct_sparks = getattr(episode, 'spark_cost_per_scene', 5)

        # --- Episode Progression ---
        status = evaluation.get("status", "going")
        turn_budget = getattr(episode, 'turn_budget', None)

        if status == "done":
            actions.suggest_next = True
        elif turn_budget and turn >= turn_budget:
            actions.suggest_next = True

        # --- Memory ---
        if status in ("closing", "done") and evaluation.get("raw_response"):
            actions.save_memory = True
            actions.memory_content = evaluation["raw_response"][:500]

        return actions

    async def execute_actions(
        self,
        actions: DirectorActions,
        session: Session,
        user_id: UUID,
    ) -> DirectorActions:
        """Execute actions, handling spark balance.

        Returns potentially modified actions (e.g., if sparks insufficient).
        """
        from app.services.credits import CreditsService, InsufficientSparksError

        credits = CreditsService.get_instance()

        # Handle scene generation with spark check
        if actions.visual_type != "none" and actions.deduct_sparks > 0:
            director_state = dict(session.director_state) if session.director_state else {}

            try:
                # Try to spend sparks
                await credits.spend(
                    user_id=user_id,
                    feature_key="auto_scene",
                    explicit_cost=actions.deduct_sparks,
                    reference_id=str(session.id),
                    metadata={"scene_hint": actions.visual_hint},
                )
                # Sparks deducted, proceed with generation

            except InsufficientSparksError:
                # Can't afford
                actions.visual_type = "none"
                actions.visual_hint = None
                actions.deduct_sparks = 0

                # Only show prompt once per episode
                if not director_state.get("spark_prompt_shown"):
                    actions.needs_sparks = True
                    director_state["spark_prompt_shown"] = True
                    # Update session state
                    await self._update_director_state(session.id, director_state)

        return actions

    async def process_exchange(
        self,
        session: Session,
        episode_template: Optional[EpisodeTemplate],
        messages: List[Dict[str, str]],
        character_id: UUID,
        user_id: UUID,
        structured_response: Optional[Dict[str, Any]] = None,
    ) -> DirectorOutput:
        """Process exchange with semantic evaluation.

        This is the unified entry point for Director processing.
        """
        # 1. Increment turn count
        new_turn_count = session.turn_count + 1

        # 2. Get character for evaluation
        character = await self._get_character(character_id)
        character_name = character.get("name", "Character") if character else "Character"

        # 3. Semantic evaluation
        if episode_template:
            evaluation = await self.evaluate_exchange(
                messages=messages,
                character_name=character_name,
                genre=getattr(episode_template, 'genre', 'romance'),
                situation=episode_template.situation or "",
                dramatic_question=episode_template.dramatic_question or "",
            )
        else:
            # Free-form chat - minimal evaluation
            evaluation = {"status": "going", "visual_type": "none", "raw_response": ""}

        # 4. Decide actions
        actions = self.decide_actions(evaluation, episode_template, session) if episode_template else DirectorActions()

        # 5. Execute actions (spark check, etc.)
        actions = await self.execute_actions(actions, session, user_id)

        # 6. Determine completion
        is_complete = actions.suggest_next
        completion_trigger = None
        if is_complete:
            if evaluation.get("status") == "done":
                completion_trigger = "semantic"
            elif episode_template and getattr(episode_template, 'turn_budget', None):
                if new_turn_count >= episode_template.turn_budget:
                    completion_trigger = "turn_limit"

        # 7. Update session state
        director_state = dict(session.director_state) if session.director_state else {}
        director_state["last_evaluation"] = {
            "status": evaluation.get("status"),
            "visual_type": evaluation.get("visual_type"),
            "turn": new_turn_count,
        }

        await self._update_session_director_state(
            session_id=session.id,
            turn_count=new_turn_count,
            director_state=director_state,
            is_complete=is_complete,
            completion_trigger=completion_trigger,
        )

        # 8. Build output
        return DirectorOutput(
            turn_count=new_turn_count,
            is_complete=is_complete,
            completion_trigger=completion_trigger,
            evaluation=evaluation,
            actions=actions,
        )

    async def _get_character(self, character_id: UUID) -> Optional[Dict[str, Any]]:
        """Get character data."""
        row = await self.db.fetch_one(
            "SELECT name, archetype FROM characters WHERE id = :character_id",
            {"character_id": str(character_id)}
        )
        return dict(row) if row else None

    async def _update_director_state(self, session_id: UUID, director_state: Dict[str, Any]):
        """Update just the director_state field."""
        await self.db.execute(
            "UPDATE sessions SET director_state = :director_state WHERE id = :session_id",
            {"director_state": json.dumps(director_state), "session_id": str(session_id)}
        )

    async def _update_session_director_state(
        self,
        session_id: UUID,
        turn_count: int,
        director_state: Dict[str, Any],
        is_complete: bool,
        completion_trigger: Optional[str],
    ):
        """Update session with Director state."""
        updates = {
            "turn_count": turn_count,
            "director_state": json.dumps(director_state),
        }

        if is_complete:
            updates["session_state"] = "complete"
            updates["completion_trigger"] = completion_trigger

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["session_id"] = str(session_id)

        await self.db.execute(
            f"UPDATE sessions SET {set_clause} WHERE id = :session_id",
            updates
        )

    async def suggest_next_episode(
        self,
        session: Session,
        evaluation: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Suggest next episode based on current session."""
        if not session.series_id:
            return None

        # Get next episode in series order
        row = await self.db.fetch_one(
            """
            SELECT
                et.id,
                et.title,
                et.slug,
                et.episode_number,
                et.situation,
                et.character_id
            FROM episode_templates et
            WHERE et.series_id = :series_id
            AND et.episode_number > :current_episode
            AND et.status = 'active'
            ORDER BY et.episode_number
            LIMIT 1
            """,
            {
                "series_id": str(session.series_id),
                "current_episode": session.episode_number if hasattr(session, 'episode_number') else 0,
            }
        )

        if not row:
            return None

        return {
            "episode_id": str(row["id"]),
            "title": row["title"],
            "slug": row["slug"],
            "episode_number": row["episode_number"],
            "situation": row["situation"],
            "character_id": str(row["character_id"]) if row["character_id"] else None,
        }
