"""Quiz Service v3.0 - LLM-based evaluation for static quizzes.

Two distinct quiz types with different viral mechanics:

1. Dating Personality Test (romantic_trope)
   - Primary mechanic: Identity validation ("this is so me")
   - Tone: Therapist who said something uncomfortable
   - Output: Psychological patterns, not preferences

2. The Unhinged Test (freak_level)
   - Primary mechanic: Social comparison ("what did you get?")
   - Tone: Chaotic friend with no filter
   - Output: Quotable roasts, screenshot-worthy content
"""

import json
import logging
import re
from typing import Any, Dict, List
from uuid import uuid4

from app.models.evaluation import (
    EvaluationType,
    ROMANTIC_TROPES,
    generate_share_id,
)
from app.services.llm import LLMService

log = logging.getLogger(__name__)


# =============================================================================
# DATING PERSONALITY TEST - Identity Validation
# =============================================================================

ROMANTIC_TROPE_CONTENT = {
    "slow_burn": {
        "title": "SLOW BURN",
        "tagline": "you use patience as protection",
        "pattern": "You've made waiting into an art form — but it's not patience. It's armor.",
        "share_text": "I'm a SLOW BURN — apparently I use patience as protection. What's your dating pattern?",
    },
    "second_chance": {
        "title": "SECOND CHANCE",
        "tagline": "you romanticize potential over reality",
        "pattern": "You're not holding out for the right person — you're holding onto the wrong one.",
        "share_text": "I'm a SECOND CHANCE — I romanticize potential over reality. What's your dating pattern?",
    },
    "all_in": {
        "title": "ALL IN",
        "tagline": "you use vulnerability as armor",
        "pattern": "You show everything upfront — not because you're brave, but because rejection early hurts less than rejection later.",
        "share_text": "I'm ALL IN — I use vulnerability as armor. What's your dating pattern?",
    },
    "push_pull": {
        "title": "PUSH & PULL",
        "tagline": "you create distance to test closeness",
        "pattern": "You call it 'keeping things interesting.' It's actually a loyalty test nobody signed up for.",
        "share_text": "I'm PUSH & PULL — I create distance to test closeness. What's your dating pattern?",
    },
    "slow_reveal": {
        "title": "SLOW REVEAL",
        "tagline": "you make people earn access as a defense",
        "pattern": "You're not mysterious. You're scared of what happens when someone actually sees you.",
        "share_text": "I'm a SLOW REVEAL — I make people earn access as a defense. What's your dating pattern?",
    },
}


# =============================================================================
# THE UNHINGED TEST - Social Comparison
# =============================================================================

FREAK_LEVELS = {
    "vanilla": {
        "title": "VANILLA BEAN",
        "tagline": "you read terms and conditions for fun",
        "description": "You're the friend who leaves parties at 10pm and actually means it when you say 'let me know you got home safe.' Your screen time is reasonable. Your Notes app is just grocery lists. Honestly? We need you to balance out the chaos.",
        "emoji": "🍦",
        "color": "text-amber-200",
        "level_number": 1,
        "share_text": "I'm VANILLA BEAN — I read terms and conditions for fun. How unhinged are you?",
    },
    "spicy": {
        "title": "SPICY CURIOUS",
        "tagline": "one foot in, one foot ready to run",
        "description": "You'll do something unhinged but you'll think about it for three days first. You've drafted texts you never sent. You've stalked but felt guilty about it. You're chaos-adjacent. Chaos-curious. The training wheels are still on but you're wobbling.",
        "emoji": "🌶️",
        "color": "text-orange-400",
        "level_number": 2,
        "share_text": "I'm SPICY CURIOUS — chaos-adjacent and wobbling. How unhinged are you?",
    },
    "unhinged": {
        "title": "CASUALLY UNHINGED",
        "tagline": "you've got stories you only tell after drink three",
        "description": "Your browser history is a liability. Your screen time report is a crime scene. You've done things that would concern your mother and texted things that would concern a therapist. But somehow you're functional. That's the scariest part.",
        "emoji": "🔥",
        "color": "text-red-500",
        "level_number": 3,
        "share_text": "I'm CASUALLY UNHINGED — functional but concerning. How unhinged are you?",
    },
    "feral": {
        "title": "ABSOLUTELY FERAL",
        "tagline": "you don't have intrusive thoughts — you ARE the intrusive thought",
        "description": "You've been banned from something. You have at least one story that starts with 'legally I can't say much but...' Your group chat fears your notification sound. You're the reason someone has trust issues and you might not even know who.",
        "emoji": "👹",
        "color": "text-purple-500",
        "level_number": 4,
        "share_text": "I'm ABSOLUTELY FERAL — I AM the intrusive thought. How unhinged are you?",
    },
    "menace": {
        "title": "CERTIFIED MENACE",
        "tagline": "the devil takes notes from you",
        "description": "You're not participating in this quiz. This quiz is studying you. Your energy has caused at least one international incident. Your presence in a room changes the WiFi. Scientists should be monitoring you. You're not unhinged — you're the hinge everyone else swings from.",
        "emoji": "😈",
        "color": "text-fuchsia-500",
        "level_number": 5,
        "share_text": "I'm a CERTIFIED MENACE — the devil takes notes from me. How unhinged are you?",
    },
}


class QuizService:
    """Service for evaluating static quizzes with LLM."""

    def __init__(self, db):
        self.db = db
        self.llm = LLMService.get_instance()

    async def evaluate_quiz(
        self,
        quiz_type: str,
        answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate quiz answers and return personalized result."""
        if quiz_type == "romantic_trope":
            return await self._evaluate_romantic_trope(answers)
        elif quiz_type == "freak_level":
            return await self._evaluate_freak_level(answers)
        else:
            raise ValueError(f"Unknown quiz type: {quiz_type}")

    # =========================================================================
    # DATING PERSONALITY TEST EVALUATION
    # Tone: Therapist who said something uncomfortable
    # =========================================================================

    async def _evaluate_romantic_trope(
        self,
        answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate dating personality test with psychological insight."""
        formatted_answers = "\n".join(
            f"Q: {a['question_text']}\nA: {a['selected_answer']} (→ {a['selected_trope']})"
            for a in answers
        )

        trope_scores = {}
        for a in answers:
            trope = a["selected_trope"]
            trope_scores[trope] = trope_scores.get(trope, 0) + 1

        trope_descriptions = "\n".join(
            f"- {key}: {data['title']} — {data['tagline']}"
            for key, data in ROMANTIC_TROPE_CONTENT.items()
        )

        prompt = f"""You are a therapist who says things that are uncomfortably accurate. Not mean — just true in a way that makes people pause.

You're analyzing someone's dating patterns based on their quiz answers. Your job is NOT to be funny or entertaining. Your job is to make them feel SEEN — to say the thing they've felt but couldn't articulate.

THE 5 DATING PATTERNS:
{trope_descriptions}

THEIR ANSWERS:
{formatted_answers}

SCORES: {json.dumps(trope_scores)}

Based on their answers, determine their primary pattern. Look at:
- What fears are driving their choices?
- What are they protecting themselves from?
- What story do they tell themselves vs. what's actually true?

Respond with this EXACT format:

TROPE: [one of: slow_burn, second_chance, all_in, push_pull, slow_reveal]
CONFIDENCE: [0.75-0.95]

THE_TRUTH: [Write 3-4 sentences that expose their pattern. Not what they DO — why they do it. This should feel like a therapist who just said something that made them put down their phone. Be specific about what their answers reveal. No fluff, no softening. Just truth.]

YOU_TELL_YOURSELF: [One sentence — the story/excuse they use. Put in quotes.]

BUT_ACTUALLY: [2 sentences — what's really going on underneath. This is the insight that makes them go "...damn."]

WHAT_YOU_NEED: [One direct sentence of advice. Not generic. Specific to their pattern.]"""

        try:
            response = await self.llm.generate(
                [{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )

            result = self._parse_romantic_trope_result(response.content)

            share_id = await self._save_evaluation(
                evaluation_type="romantic_trope",
                result=result,
            )

            return {
                "evaluation_type": "romantic_trope",
                "result": result,
                "share_id": share_id,
            }

        except Exception as e:
            log.error(f"Romantic trope evaluation failed: {e}")
            return await self._fallback_romantic_trope(trope_scores)

    def _parse_romantic_trope_result(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for dating personality test."""
        # Extract trope
        trope_match = re.search(r'TROPE:\s*(\w+)', response, re.IGNORECASE)
        trope = trope_match.group(1).lower() if trope_match else "slow_burn"

        valid_tropes = list(ROMANTIC_TROPE_CONTENT.keys())
        if trope not in valid_tropes:
            trope = "slow_burn"

        # Extract confidence
        conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        confidence = float(conf_match.group(1)) if conf_match else 0.85
        confidence = max(0.0, min(1.0, confidence))

        # Extract the_truth
        truth_match = re.search(r'THE_TRUTH:\s*([^\n]+(?:\n(?![A-Z_]+:)[^\n]+)*)', response, re.IGNORECASE)
        the_truth = truth_match.group(1).strip() if truth_match else None

        # Extract you_tell_yourself
        tell_match = re.search(r'YOU_TELL_YOURSELF:\s*([^\n]+)', response, re.IGNORECASE)
        you_tell_yourself = tell_match.group(1).strip().strip('"') if tell_match else None

        # Extract but_actually
        but_match = re.search(r'BUT_ACTUALLY:\s*([^\n]+(?:\n(?![A-Z_]+:)[^\n]+)*)', response, re.IGNORECASE)
        but_actually = but_match.group(1).strip() if but_match else None

        # Extract what_you_need
        need_match = re.search(r'WHAT_YOU_NEED:\s*([^\n]+)', response, re.IGNORECASE)
        what_you_need = need_match.group(1).strip() if need_match else None

        trope_data = ROMANTIC_TROPE_CONTENT.get(trope, ROMANTIC_TROPE_CONTENT["slow_burn"])

        return {
            "trope": trope,
            "confidence": confidence,
            "title": trope_data["title"],
            "tagline": trope_data["tagline"],
            "pattern": trope_data["pattern"],
            "share_text": trope_data.get("share_text", ""),
            # LLM-generated personalized content
            "the_truth": the_truth,
            "you_tell_yourself": you_tell_yourself,
            "but_actually": but_actually,
            "what_you_need": what_you_need,
        }

    async def _fallback_romantic_trope(
        self,
        trope_scores: Dict[str, int],
    ) -> Dict[str, Any]:
        """Fallback evaluation when LLM fails."""
        if not trope_scores:
            trope = "slow_burn"
        else:
            trope = max(trope_scores, key=trope_scores.get)

        trope_data = ROMANTIC_TROPE_CONTENT.get(trope, ROMANTIC_TROPE_CONTENT["slow_burn"])

        result = {
            "trope": trope,
            "confidence": 0.75,
            "title": trope_data["title"],
            "tagline": trope_data["tagline"],
            "pattern": trope_data["pattern"],
            "share_text": trope_data.get("share_text", ""),
            "the_truth": None,
            "you_tell_yourself": None,
            "but_actually": None,
            "what_you_need": None,
        }

        share_id = await self._save_evaluation(
            evaluation_type="romantic_trope",
            result=result,
        )

        return {
            "evaluation_type": "romantic_trope",
            "result": result,
            "share_id": share_id,
        }

    # =========================================================================
    # THE UNHINGED TEST EVALUATION
    # Tone: Chaotic friend with no filter
    # =========================================================================

    async def _evaluate_freak_level(
        self,
        answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate unhinged test with maximum chaos energy."""
        formatted_answers = "\n".join(
            f"Q: {a['question_text']}\nA: {a['selected_answer']} (→ {a['selected_trope']})"
            for a in answers
        )

        level_scores = {}
        for a in answers:
            level = a["selected_trope"]
            level_scores[level] = level_scores.get(level, 0) + 1

        level_descriptions = "\n".join(
            f"- {key} (level {data['level_number']}): {data['title']} — {data['tagline']}"
            for key, data in FREAK_LEVELS.items()
        )

        prompt = f"""You are someone's most unhinged friend who has absolutely no filter. You're reading their quiz answers and you're about to ROAST them (lovingly).

This is NOT a therapy session. This is pure entertainment. Your goal is to make them:
1. Screenshot this immediately
2. Send it to their group chat
3. Say "WHY IS THIS SO ACCURATE"

THE 5 UNHINGED LEVELS (1=mild, 5=menace):
{level_descriptions}

THEIR ANSWERS:
{formatted_answers}

SCORES: {json.dumps(level_scores)}

Pick their level based on overall vibe, not just raw scores. Someone who picked ONE menace answer might still be a menace.

Respond with this EXACT format:

LEVEL: [one of: vanilla, spicy, unhinged, feral, menace]
CONFIDENCE: [0.75-0.95]

ROAST_1: [Call out a specific answer pattern. Be unhinged. Max 20 words. Example: "You said you'd 'check their profile twice' — bestie that's surveillance."]

ROAST_2: [Another specific callout from their answers. Make it hit. Max 20 words.]

ROAST_3: [The devastating closer. This one should make them screenshot. Max 20 words.]

VIBE_CHECK: [One absolutely unhinged sentence summarizing their energy. This should be quotable. Think "your screen time is a war crime" or "you don't have red flags, you ARE the red flag." Max 25 words.]"""

        try:
            response = await self.llm.generate(
                [{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.85,
            )

            result = self._parse_freak_level_result(response.content)

            share_id = await self._save_evaluation(
                evaluation_type="freak_level",
                result=result,
            )

            return {
                "evaluation_type": "freak_level",
                "result": result,
                "share_id": share_id,
            }

        except Exception as e:
            log.error(f"Freak level evaluation failed: {e}")
            return await self._fallback_freak_level(level_scores)

    def _parse_freak_level_result(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for unhinged test."""
        # Extract level
        level_match = re.search(r'LEVEL:\s*(\w+)', response, re.IGNORECASE)
        level = level_match.group(1).lower() if level_match else "unhinged"

        valid_levels = list(FREAK_LEVELS.keys())
        if level not in valid_levels:
            level = "unhinged"

        # Extract confidence
        conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        confidence = float(conf_match.group(1)) if conf_match else 0.85
        confidence = max(0.0, min(1.0, confidence))

        # Extract roasts
        evidence = []
        for i in range(1, 4):
            roast_match = re.search(rf'ROAST_{i}:\s*([^\n]+)', response, re.IGNORECASE)
            if roast_match:
                evidence.append(roast_match.group(1).strip())

        # Extract vibe check
        vibe_match = re.search(r'VIBE_CHECK:\s*([^\n]+)', response, re.IGNORECASE)
        vibe_check = vibe_match.group(1).strip() if vibe_match else None

        level_data = FREAK_LEVELS.get(level, FREAK_LEVELS["unhinged"])

        return {
            "level": level,
            "confidence": confidence,
            "title": level_data["title"],
            "tagline": level_data["tagline"],
            "description": level_data["description"],
            "emoji": level_data["emoji"],
            "color": level_data["color"],
            "level_number": level_data["level_number"],
            "share_text": level_data.get("share_text", ""),
            # LLM-generated personalized content
            "evidence": evidence,
            "vibe_check": vibe_check,
        }

    async def _fallback_freak_level(
        self,
        level_scores: Dict[str, int],
    ) -> Dict[str, Any]:
        """Fallback evaluation when LLM fails."""
        if not level_scores:
            level = "unhinged"
        else:
            level = max(level_scores, key=level_scores.get)

        level_data = FREAK_LEVELS.get(level, FREAK_LEVELS["unhinged"])

        result = {
            "level": level,
            "confidence": 0.75,
            "title": level_data["title"],
            "tagline": level_data["tagline"],
            "description": level_data["description"],
            "emoji": level_data["emoji"],
            "color": level_data["color"],
            "level_number": level_data["level_number"],
            "share_text": level_data.get("share_text", ""),
            "evidence": [],
            "vibe_check": None,
        }

        share_id = await self._save_evaluation(
            evaluation_type="freak_level",
            result=result,
        )

        return {
            "evaluation_type": "freak_level",
            "result": result,
            "share_id": share_id,
        }

    # =========================================================================
    # SHARED UTILITIES
    # =========================================================================

    async def _save_evaluation(
        self,
        evaluation_type: str,
        result: Dict[str, Any],
    ) -> str:
        """Save evaluation to database and return share_id."""
        evaluation_id = uuid4()
        share_id = generate_share_id()

        try:
            await self.db.execute(
                """
                INSERT INTO session_evaluations (
                    id, session_id, evaluation_type, result, share_id, created_at
                ) VALUES (
                    :id, NULL, :evaluation_type, :result, :share_id, NOW()
                )
                """,
                {
                    "id": str(evaluation_id),
                    "evaluation_type": evaluation_type,
                    "result": json.dumps(result),
                    "share_id": share_id,
                }
            )
        except Exception as e:
            log.error(f"Failed to save evaluation: {e}")

        return share_id
