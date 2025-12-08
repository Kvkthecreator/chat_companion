#!/usr/bin/env python3
"""
Canon-Compliant P3 Reflection Agent - V3.0
Implements YARNNN_REFLECTION_READMODEL.md specification exactly

Sacred Rules:
1. Input: Text window (raw_dumps) + Graph window (blocks + relationships)
2. Scope: Basket-scoped only (no workspace-wide queries)
3. Output: Artifacts only, never substrate mutations
4. Pure read-only substrate analysis

V3.0 Changes:
- Query unified blocks table (no context_items)
- Entity blocks identified by semantic_type='entity'
- All substrate is blocks with knowledge/meaning/structural types
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from app.services.basket_signatures import (
    build_signature_payload,
    upsert_basket_signature,
)
from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.llm import get_llm


class ReflectionComputationRequest(BaseModel):
    """Request to compute reflections from workspace substrate."""
    workspace_id: UUID
    basket_id: Optional[UUID] = None
    reflection_types: List[str] = Field(default=["patterns", "insights", "gaps"])
    agent_id: str
    substrate_window_hours: Optional[int] = None


class ReflectionComputationResult(BaseModel):
    """Result of reflection computation."""
    workspace_id: str  # JSON serializable
    basket_id: Optional[str] = None  # JSON serializable
    reflections_created: int
    computation_timestamp: str
    reflection_text: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

class CanonP3ReflectionAgent:
    """Canon-compliant P3 Reflection Agent following YARNNN_REFLECTION_READMODEL.md"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm = get_llm()
        
    async def compute_reflections(self, request: ReflectionComputationRequest) -> ReflectionComputationResult:
        """
        V3.0: Canon-compliant reflection computation:
        - Text window: last N raw_dumps in basket
        - Graph window: blocks + substrate_relationships touching those dumps
        - Output: Reflection artifacts only

        All substrate is now unified blocks (no context_items).
        """
        if not request.basket_id:
            raise ValueError("P3 Reflection requires basket_id - canon mandates basket-scoped analysis")

        try:
            # CANON STEP 1: Get text window (raw_dumps in basket) with optional time constraint
            text_window = self._get_text_window(request.basket_id, request.substrate_window_hours)

            if not text_window:
                self.logger.info(f"P3 Reflection: No raw_dumps found in basket {request.basket_id}")
                return ReflectionComputationResult(
                    workspace_id=str(request.workspace_id),
                    basket_id=str(request.basket_id),
                    reflections_created=0,
                    computation_timestamp=datetime.utcnow().isoformat(),
                    reflection_text="No memory substrate available for reflection",
                    meta={"substrate_dump_count": 0, "canon_compliant": True}
                )

            # CANON STEP 2: Get graph window (V3.0: blocks + relationships touching text window)
            graph_window = self._get_graph_window(request.basket_id, text_window)
            
            # Canon: Collect substrate ids for idempotent storage
            substrate_ids = sorted({str(dump.get("id")) for dump in text_window if dump.get("id")})
            window_bounds = self._compute_window_bounds(text_window)

            batch = await self._generate_structured_reflections(
                request,
                text_window,
                graph_window,
                substrate_ids,
                window_bounds,
            )

            artifacts_created = 0
            created_ids: List[str] = []
            sample_text: Optional[str] = None

            for reflection in batch.get("reflections", []):
                stored_id = self._store_reflection_artifact(
                    request,
                    reflection,
                    substrate_ids,
                    window_bounds,
                )
                if stored_id:
                    artifacts_created += 1
                    created_ids.append(str(stored_id))
                    if sample_text is None:
                        sample_text = reflection.get("text")

            if artifacts_created == 0:
                # Fall back to legacy heuristic artifact to avoid empty responses
                legacy_artifact = self._compute_reflection_artifact(text_window, graph_window)
                stored_id = self._store_reflection_artifact(
                    request,
                    {
                        "text": legacy_artifact["text"],
                        "meta": {
                            "engine": "fallback_heuristic",
                            "patterns": legacy_artifact.get("patterns", []),
                            "source_count": legacy_artifact.get("source_count", 0),
                            "connection_count": legacy_artifact.get("connection_count", 0),
                        },
                        "hash_key": "legacy",
                    },
                    substrate_ids,
                    window_bounds,
                )
                if stored_id:
                    artifacts_created = 1
                    created_ids.append(str(stored_id))
                    sample_text = legacy_artifact["text"]

            meta_payload: Dict[str, Any] = {
                "substrate_dump_count": len(text_window),
                "graph_elements": len(graph_window),
                "canon_compliant": True,
                "window_model": "text+graph",
            }
            if created_ids:
                meta_payload["artifact_ids"] = created_ids

            if batch.get("summary"):
                meta_payload["summary"] = batch["summary"]
            if batch.get("raw"):
                meta_payload["structured_output"] = batch["raw"]
            if batch.get("usage"):
                meta_payload["llm_usage"] = batch["usage"]

            try:
                self._update_basket_signature(
                    request=request,
                    summary=meta_payload.get("summary") or sample_text or "",
                    reflections=batch.get("reflections", []),
                    text_window=text_window,
                    source_reflection_id=created_ids[0] if created_ids else None,
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "Failed to update basket signature for %s: %s",
                    request.basket_id,
                    exc,
                )

            return ReflectionComputationResult(
                workspace_id=str(request.workspace_id),
                basket_id=str(request.basket_id),
                reflections_created=artifacts_created,
                computation_timestamp=datetime.utcnow().isoformat(),
                reflection_text=sample_text,
                meta=meta_payload,
            )
            
        except Exception as e:
            self.logger.error(f"Canon P3 Reflection failed for basket {request.basket_id}: {e}")
            raise

    def _update_basket_signature(
        self,
        *,
        request: ReflectionComputationRequest,
        summary: Optional[str],
        reflections: List[Dict[str, Any]],
        text_window: List[Dict[str, Any]],
        source_reflection_id: Optional[str],
    ) -> None:
        if not request.workspace_id or not request.basket_id:
            return

        payload = build_signature_payload(
            workspace_id=str(request.workspace_id),
            basket_id=str(request.basket_id),
            summary=summary or "",
            reflections=reflections,
            text_window=text_window,
            source_reflection_id=source_reflection_id,
        )

        if not payload:
            return

        upsert_basket_signature(payload)

    def _get_text_window(self, basket_id: UUID, window_hours: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Canon: Text window = last N raw_dumps in basket with optional time constraint"""
        try:
            query = supabase.table("raw_dumps").select(
                "id,basket_id,text_dump,body_md,file_url,created_at,source_meta"
            ).eq("basket_id", str(basket_id))
            
            # Apply time window constraint if specified
            if window_hours is not None:
                cutoff_time = datetime.utcnow() - timedelta(hours=window_hours)
                query = query.gte("created_at", cutoff_time.isoformat())
            
            response = query.order(
                "created_at", desc=True
            ).limit(limit).execute()
            
            dumps = response.data or []
            # Exclude tombstoned (archived/redacted/deleted)
            try:
                t = supabase.table("substrate_tombstones").select("substrate_id").eq("basket_id", str(basket_id)).eq("substrate_type", "dump").execute()
                if t.data:
                    excluded = {row["substrate_id"] for row in t.data}
                    dumps = [d for d in dumps if d.get("id") not in excluded]
            except Exception:
                pass
            return dumps
            
        except Exception as e:
            self.logger.error(f"Failed to get text window: {e}")
            return []
    
    def _get_graph_window(self, basket_id: UUID, text_window: List[Dict]) -> List[Dict[str, Any]]:
        """
        V3.0: Graph window = blocks + relationships touching text window

        Queries unified blocks table for all substrate (knowledge, meaning, structural types).
        """
        try:
            graph_elements: List[Dict[str, Any]] = []
            dump_ids = {str(dump.get("id")) for dump in text_window if dump.get("id")}

            # V3.0: Collect blocks linked to the dump window
            blocks_query = supabase.table("blocks").select(
                "id,basket_id,semantic_type,title,content,anchor_role,confidence_score,raw_dump_id,metadata,created_at"
            ).eq("basket_id", str(basket_id)).neq("state", "REJECTED")

            if dump_ids:
                try:
                    blocks_query = blocks_query.in_("raw_dump_id", list(dump_ids))
                except Exception:
                    # Some blocks may not track raw_dump_id; fall back to basket scope
                    pass

            blocks_response = blocks_query.limit(50).execute()

            block_ids: List[str] = []
            if blocks_response.data:
                for block in blocks_response.data:
                    element = {**block, "element_type": "block"}  # V3.0: All substrate is blocks
                    graph_elements.append(element)
                    block_id = str(block.get("id")) if block.get("id") else None
                    if block_id:
                        block_ids.append(block_id)

            relevant_ids = set(dump_ids)
            relevant_ids.update(block_ids)

            # Collect relationships that touch either dumps or derived blocks
            relationships_response = supabase.table("substrate_relationships").select(
                "id,basket_id,from_type,from_id,to_type,to_id,relationship_type,strength,description,created_at"
            ).eq("basket_id", str(basket_id)).limit(200).execute()

            if relationships_response.data:
                for rel in relationships_response.data:
                    from_id = str(rel.get("from_id")) if rel.get("from_id") else None
                    to_id = str(rel.get("to_id")) if rel.get("to_id") else None
                    if not relevant_ids or (from_id in relevant_ids or to_id in relevant_ids):
                        graph_elements.append({**rel, "element_type": "relationship"})

            return graph_elements

        except Exception as e:
            self.logger.error(f"Failed to get graph window: {e}")
            return []

    def _compute_window_bounds(self, text_window: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        timestamps: List[str] = []
        for dump in text_window:
            raw = dump.get("created_at")
            if not raw:
                continue
            try:
                if isinstance(raw, datetime):
                    timestamps.append(raw.isoformat())
                else:
                    raw_str = str(raw)
                    # Normalize trailing Z to offset format accepted by fromisoformat
                    normalized = raw_str.replace("Z", "+00:00") if "Z" in raw_str else raw_str
                    timestamps.append(datetime.fromisoformat(normalized).isoformat())
            except Exception:
                timestamps.append(str(raw))

        if not timestamps:
            return (None, None)

        return (min(timestamps), max(timestamps))

    def _build_window_payload(
        self,
        text_window: List[Dict[str, Any]],
        graph_window: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        payload: List[Dict[str, Any]] = []
        evidence_lookup: Dict[str, Dict[str, Any]] = {}

        trimmed_text_window = text_window[:12]
        for idx, dump in enumerate(trimmed_text_window):
            dump_id = str(dump.get("id")) if dump.get("id") else None
            snippet = self._clean_snippet(dump.get("text_dump") or dump.get("body_md") or "")
            label = self._derive_dump_label(dump, idx)
            entry = {
                "id": dump_id,
                "kind": "raw_dump",
                "label": label,
                "created_at": dump.get("created_at"),
                "snippet": snippet,
            }
            if dump.get("file_url"):
                entry["file"] = str(dump["file_url"]).split("/")[-1]
            payload.append(entry)
            if dump_id:
                evidence_lookup[dump_id] = {
                    "id": dump_id,
                    "kind": "raw_dump",
                    "label": label,
                    "snippet": snippet,
                    "created_at": dump.get("created_at"),
                }

        # V3.0: Blocks (all substrate types: knowledge, meaning, structural)
        blocks = [item for item in graph_window if item.get("element_type") == "block"]
        for block in blocks[:30]:
            block_id = str(block.get("id")) if block.get("id") else None
            content = block.get("content") or ""
            snippet = self._clean_snippet(content, limit=280)
            entry = {
                "id": block_id,
                "kind": "block",  # V3.0: All substrate is blocks
                "title": block.get("title") or "Untitled Block",
                "semantic_type": block.get("semantic_type"),  # V3.0: knowledge/meaning/structural
                "anchor_role": block.get("anchor_role"),  # V3.0: Emergent anchor
                "snippet": snippet,
                "raw_dump_id": block.get("raw_dump_id"),
            }
            payload.append(entry)
            if block_id:
                evidence_lookup[block_id] = {
                    "id": block_id,
                    "kind": "block",  # V3.0
                    "label": entry["title"],
                    "snippet": snippet,
                    "raw_dump_id": block.get("raw_dump_id"),
                }

        relationships = [item for item in graph_window if item.get("element_type") == "relationship"]
        for rel in relationships[:30]:
            rel_id = str(rel.get("id")) if rel.get("id") else None
            entry = {
                "id": rel_id,
                "kind": "relationship",
                "from_id": str(rel.get("from_id")) if rel.get("from_id") else None,
                "to_id": str(rel.get("to_id")) if rel.get("to_id") else None,
                "relationship_type": rel.get("relationship_type"),
                "description": self._clean_snippet(rel.get("description") or "", limit=160),
            }
            payload.append(entry)

        return payload, evidence_lookup

    def _clean_snippet(self, text: Optional[str], limit: int = 480) -> str:
        if not text:
            return ""
        collapsed = " ".join(text.strip().split())
        if len(collapsed) <= limit:
            return collapsed
        truncated = collapsed[:limit].rsplit(" ", 1)[0].rstrip(",.;")
        return f"{truncated}..."

    def _derive_dump_label(self, dump: Dict[str, Any], index: int) -> str:
        source_meta = dump.get("source_meta") or {}
        if isinstance(source_meta, dict):
            title = source_meta.get("title") or source_meta.get("name")
            if title:
                return str(title)
        file_url = dump.get("file_url")
        if file_url:
            return str(file_url).split("/")[-1]
        created_at = dump.get("created_at")
        if created_at:
            return f"Entry {index + 1} ({str(created_at)[:10]})"
        return f"Entry {index + 1}"

    async def _generate_structured_reflections(
        self,
        request: ReflectionComputationRequest,
        text_window: List[Dict[str, Any]],
        graph_window: List[Dict[str, Any]],
        substrate_ids: List[str],
        window_bounds: Tuple[Optional[str], Optional[str]],
    ) -> Dict[str, Any]:
        payload, evidence_lookup = self._build_window_payload(text_window, graph_window)

        if not payload:
            return {"reflections": [], "summary": None, "raw": None, "usage": None}

        payload_json = json.dumps(payload, ensure_ascii=False)
        window_start, window_end = window_bounds

        prompt = (
            "You are YARNNN's P3 Reflection agent. Analyze the user's actual work "
            "and surface insights that feel specific, actionable, and grounded in what they wrote.\n"
            "Speak directly about their content. Never mention system concepts like substrate, dumps, or graphs.\n"
            "Each insight must cite evidence ids from the provided items.\n"
            "Return JSON following the p3_reflection schema.\n"
            f"Workspace: {request.workspace_id}\n"
            f"Basket: {request.basket_id}\n"
            f"Window start: {window_start or 'unknown'}\n"
            f"Window end: {window_end or 'unknown'}\n"
            "Input items (JSON array):\n"
            f"{payload_json}"
        )

        try:
            response = await self.llm.get_json_response(
                prompt,
                temperature=1.0,  # Use default temperature for model compatibility
                max_tokens=2200,
                schema_name="p3_reflection",
            )
        except Exception as e:
            self.logger.warning(f"LLM reflection generation failed: {e}")
            return {"reflections": [], "summary": None, "raw": None, "usage": None}

        if not response.success or not response.parsed:
            self.logger.warning("LLM reflection returned no structured output")
            return {"reflections": [], "summary": None, "raw": None, "usage": response.usage}

        parsed = response.parsed or {}
        reflections = self._normalize_llm_reflections(parsed, evidence_lookup, window_bounds, substrate_ids)

        summary = (parsed.get("summary") or "").strip() or None

        return {
            "reflections": reflections,
            "summary": summary,
            "raw": parsed,
            "usage": response.usage,
        }

    def _normalize_llm_reflections(
        self,
        parsed: Dict[str, Any],
        evidence_lookup: Dict[str, Dict[str, Any]],
        window_bounds: Tuple[Optional[str], Optional[str]],
        substrate_ids: List[str],
    ) -> List[Dict[str, Any]]:
        reflections: List[Dict[str, Any]] = []

        summary_text = (parsed.get("summary") or "").strip()
        if summary_text:
            headline, body = self._split_headline_body(summary_text)
            reflections.append(
                self._format_reflection(
                    kind="overview",
                    headline=headline or "What stands out",
                    body=body,
                    supporting_ids=[],
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={"confidence": parsed.get("confidence_overall")},
                )
            )

        patterns = parsed.get("patterns") or []
        for pattern in patterns[:3]:
            description = (pattern.get("description") or "").strip()
            if not description:
                continue
            headline, body = self._split_headline_body(description)
            supporting_ids = self._sanitize_evidence_ids(pattern.get("evidence_ids"), evidence_lookup, substrate_ids)
            reflections.append(
                self._format_reflection(
                    kind="pattern",
                    headline=headline or "Pattern detected",
                    body=body,
                    supporting_ids=supporting_ids,
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={
                        "pattern_type": pattern.get("type"),
                        "confidence": pattern.get("confidence"),
                    },
                )
            )

        tensions = parsed.get("tensions") or []
        for tension in tensions[:2]:
            description = (tension.get("description") or "").strip()
            if not description:
                continue
            headline, body = self._split_headline_body(description)
            supporting_ids = self._sanitize_evidence_ids(tension.get("evidence_ids"), evidence_lookup, substrate_ids)
            reflections.append(
                self._format_reflection(
                    kind="tension",
                    headline=headline or "Competing priorities",
                    body=body,
                    supporting_ids=supporting_ids,
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={"severity": tension.get("severity")},
                )
            )

        opportunities = parsed.get("opportunities") or []
        for opportunity in opportunities[:2]:
            description = (opportunity.get("description") or "").strip()
            if not description:
                continue
            headline, body = self._split_headline_body(description)
            supporting_ids = self._sanitize_evidence_ids(opportunity.get("evidence_ids"), evidence_lookup, substrate_ids)
            reflections.append(
                self._format_reflection(
                    kind="opportunity",
                    headline=headline or "Opportunity spotted",
                    body=body or opportunity.get("suggested_action", ""),
                    supporting_ids=supporting_ids,
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={
                        "suggested_action": opportunity.get("suggested_action"),
                    },
                )
            )

        questions = parsed.get("questions") or []
        for question in questions[:2]:
            description = (question.get("description") or "").strip()
            if not description:
                continue
            headline, body = self._split_headline_body(description)
            supporting_ids = self._sanitize_evidence_ids(question.get("evidence_ids"), evidence_lookup, substrate_ids)
            reflections.append(
                self._format_reflection(
                    kind="question",
                    headline=headline or "Open question",
                    body=body,
                    supporting_ids=supporting_ids,
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={"priority": question.get("priority")},
                )
            )

        recommendations = parsed.get("recommendations") or []
        for recommendation in recommendations[:2]:
            description = (recommendation.get("description") or "").strip()
            if not description:
                continue
            headline, body = self._split_headline_body(description)
            supporting_ids = self._sanitize_evidence_ids(recommendation.get("evidence_ids"), evidence_lookup, substrate_ids)
            reflections.append(
                self._format_reflection(
                    kind="recommendation",
                    headline=headline or "Next step",
                    body=body or recommendation.get("rationale", ""),
                    supporting_ids=supporting_ids,
                    evidence_lookup=evidence_lookup,
                    window_bounds=window_bounds,
                    extra_meta={"rationale": recommendation.get("rationale")},
                )
            )

        # Keep list compact and deterministic
        return reflections[:6]

    def _sanitize_evidence_ids(
        self,
        evidence_ids: Optional[List[Any]],
        evidence_lookup: Dict[str, Dict[str, Any]],
        substrate_ids: List[str],
    ) -> List[str]:
        sanitized: List[str] = []
        for value in evidence_ids or []:
            evid = str(value).strip()
            if not evid or evid in sanitized:
                continue
            if evid in evidence_lookup:
                sanitized.append(evid)
        if not sanitized and substrate_ids:
            sanitized.append(substrate_ids[0])
        return sanitized[:3]

    def _split_headline_body(self, text: str) -> Tuple[str, str]:
        if not text:
            return "", ""
        simplified = text.strip()
        if len(simplified) <= 110:
            return simplified, ""
        parts = simplified.split(". ", 1)
        if len(parts) == 1:
            return simplified, ""
        headline = parts[0].strip().rstrip(".")
        body = parts[1].strip()
        return headline, body

    def _format_reflection(
        self,
        *,
        kind: str,
        headline: str,
        body: str,
        supporting_ids: List[str],
        evidence_lookup: Dict[str, Dict[str, Any]],
        window_bounds: Tuple[Optional[str], Optional[str]],
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        evidence_details: List[Dict[str, Any]] = []
        for evid in supporting_ids:
            info = evidence_lookup.get(evid)
            if info:
                evidence_details.append(info)

        text_parts = [headline.strip()] if headline else []
        if body:
            text_parts.append(body.strip())
        payload_text = "\n\n".join(part for part in text_parts if part)

        meta_payload: Dict[str, Any] = {
            "type": kind,
            "headline": headline.strip() if headline else "",
            "body": body.strip() if body else "",
            "supporting_ids": supporting_ids,
            "supporting_evidence": evidence_details,
            "window": {
                "start": window_bounds[0],
                "end": window_bounds[1],
            },
            "engine": "p3_llm_v2",
        }
        if extra_meta:
            meta_payload.update({k: v for k, v in extra_meta.items() if v is not None})

        hash_key = self._make_hash_key(kind, headline, body, supporting_ids)

        return {
            "text": payload_text or headline or body,
            "meta": meta_payload,
            "hash_key": hash_key,
        }

    def _make_hash_key(self, kind: str, headline: str, body: str, supporting_ids: List[str]) -> str:
        raw = "|".join(filter(None, [kind, headline, body] + supporting_ids))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return digest[:16]

    def _compute_reflection_artifact(self, text_window: List[Dict], graph_window: List[Dict]) -> Dict[str, Any]:
        """
        Canon: Pure computation following YARNNN_REFLECTIONS_UX_CANON.md
        Focus on user content, not system structure
        """
        
        dump_count = len(text_window)
        graph_count = len(graph_window)
        
        # Analyze actual user content for meaningful patterns
        text_content = []
        file_names = []
        for dump in text_window:
            if dump.get("text_dump"):
                text_content.append(dump["text_dump"])
            # Extract file names if available for context
            if dump.get("file_url"):
                file_names.append(dump.get("file_url", "").split('/')[-1])
        
        combined_text = " ".join(text_content)
        
        # Look for user-meaningful patterns in their actual content
        reflection_text = self._generate_user_centric_insight(combined_text, file_names, dump_count, graph_count)
        
        return {
            "text": reflection_text,
            "patterns": self._extract_content_themes(combined_text),
            "source_count": dump_count,
            "connection_count": graph_count,
            "computation_method": "user_content_analysis"
        }
    
    def _generate_user_centric_insight(self, content: str, file_names: List[str], dump_count: int, graph_count: int) -> str:
        """Generate deep, actionable insights using advanced pattern recognition"""
        
        content_lower = content.lower()
        
        # Advanced insight generation based on YARNNN's intelligence objectives
        insights = self._analyze_deep_patterns(content_lower, dump_count, graph_count)
        tensions = self._identify_tensions_and_contradictions(content_lower)
        trajectory = self._analyze_thinking_trajectory(content_lower, dump_count)
        gaps = self._identify_critical_gaps(content_lower)
        
        # Prioritize insights by value
        if tensions:
            return tensions
        elif trajectory:
            return trajectory
        elif insights:
            return insights
        elif gaps:
            return gaps
        
        # Sophisticated default based on substrate richness
        if graph_count > 10:
            return f"Your knowledge graph shows {graph_count} connections across {dump_count} items. The density suggests you're building a comprehensive understanding - consider documenting the key relationships you're discovering."
        elif dump_count >= 5:
            return f"With {dump_count} memories captured, patterns are emerging. Your thinking shows signs of convergence around key themes - now might be a good time to synthesize these insights into action."
        elif dump_count >= 2:
            return f"Early patterns detected across {dump_count} items. Continue building your knowledge base to unlock deeper insights about your thinking trajectory."
        else:
            return "Your knowledge garden is just beginning. Each memory you add creates potential for discovering unexpected connections."
    
    def _analyze_deep_patterns(self, content: str, dump_count: int, graph_count: int) -> str:
        """Analyze deep patterns using multiple signals"""
        
        # Strategic pattern detection
        strategic_indicators = ["strategy", "plan", "roadmap", "vision", "objective", "milestone"]
        execution_indicators = ["implement", "execute", "deliver", "build", "launch", "ship"]
        strategic_count = sum(1 for ind in strategic_indicators if ind in content)
        execution_count = sum(1 for ind in execution_indicators if ind in content)
        
        if strategic_count > 3 and execution_count < 2:
            return f"Pattern detected: Heavy strategic planning ({strategic_count} indicators) with limited execution focus. Your thinking is in 'planning mode' - consider identifying one concrete next action to bridge strategy to execution."
        
        # Innovation vs optimization pattern
        innovation_words = ["new", "novel", "innovative", "disrupt", "transform", "reimagine", "breakthrough"]
        optimization_words = ["improve", "enhance", "optimize", "refine", "iterate", "polish", "streamline"]
        innovation_score = sum(1 for word in innovation_words if word in content)
        optimization_score = sum(1 for word in optimization_words if word in content)
        
        if innovation_score > optimization_score * 2:
            return f"Your thinking leans heavily toward innovation over optimization ({innovation_score}:{optimization_score} ratio). This suggests you're in exploration mode - perfect for breakthrough thinking, but remember to validate ideas with small experiments."
        elif optimization_score > innovation_score * 2:
            return f"You're focused on optimization and refinement ({optimization_score}:{innovation_score} ratio). This disciplined approach yields consistent improvements - but occasionally stepping back for radical rethinking can unlock new possibilities."
        
        # Complexity emergence pattern
        concept_density = len(set(content.split())) / len(content.split()) if content.split() else 0
        if concept_density > 0.7 and dump_count > 3:
            return f"High conceptual density detected ({concept_density:.1%} unique terms). Your thinking is becoming increasingly sophisticated - this complexity suggests you're ready to identify the core principles that tie everything together."
        
        # Network effects pattern
        if graph_count > dump_count * 2:
            connection_ratio = graph_count / dump_count
            return f"Exceptional connectivity in your knowledge graph ({connection_ratio:.1f} connections per item). You're discovering relationships others might miss - this network thinking is your superpower for innovative solutions."
        
        return ""
    
    def _identify_tensions_and_contradictions(self, content: str) -> str:
        """Identify productive tensions that drive insight"""
        
        # Speed vs Quality tension
        speed_words = ["fast", "quick", "rapid", "urgent", "asap", "immediately", "now"]
        quality_words = ["quality", "excellence", "perfect", "thorough", "comprehensive", "detailed"]
        has_speed = any(word in content for word in speed_words)
        has_quality = any(word in content for word in quality_words)
        
        if has_speed and has_quality:
            return "Tension detected: You're balancing speed with quality. This classic dilemma often resolves through iteration - ship fast to learn, then refine based on real feedback. Which can you prototype first?"
        
        # Scale vs Personalization tension
        scale_words = ["scale", "growth", "expand", "automate", "systematic", "platform"]
        personal_words = ["personal", "custom", "individual", "bespoke", "tailored", "unique"]
        has_scale = any(word in content for word in scale_words)
        has_personal = any(word in content for word in personal_words)
        
        if has_scale and has_personal:
            return "Strategic tension: Scaling while maintaining personalization. The most successful approaches often find the 'scalable personal' - what core elements can you standardize while keeping key touchpoints human?"
        
        # Innovation vs Stability tension
        change_words = ["change", "new", "transform", "disrupt", "revolutionize", "reimagine"]
        stability_words = ["stable", "reliable", "consistent", "proven", "established", "maintain"]
        has_change = any(word in content for word in change_words)
        has_stability = any(word in content for word in stability_words)
        
        if has_change and has_stability:
            return "Core tension: Innovation versus stability. This productive friction often leads to 'stable innovation' - changing HOW you do things while keeping WHAT you deliver consistent. Where can you innovate behind the scenes?"
        
        return ""
    
    def _analyze_thinking_trajectory(self, content: str, dump_count: int) -> str:
        """Analyze the evolution and trajectory of thinking"""
        
        # Convergence detection
        question_marks = content.count('?')
        exclamation_marks = content.count('!')
        
        if dump_count >= 3:
            if question_marks > exclamation_marks * 2:
                return f"Trajectory: Your thinking is in active exploration mode ({question_marks} questions captured). This questioning phase is crucial for breakthrough insights - keep probing until patterns crystallize."
            elif exclamation_marks > question_marks:
                return f"Trajectory: You're moving from questions to insights ({exclamation_marks} key realizations). This convergence suggests you're ready to test your hypotheses in reality."
        
        # Evolution detection
        temporal_words = ["initially", "then", "now", "evolved", "changed", "realized", "discovered"]
        evolution_count = sum(1 for word in temporal_words if word in content)
        
        if evolution_count >= 3:
            return f"Your thinking shows clear evolution ({evolution_count} transition markers). This intellectual growth trajectory suggests you're integrating new perspectives - document this journey, as the path often matters more than the destination."
        
        # Depth detection
        because_count = content.count("because")
        therefore_count = content.count("therefore")
        reasoning_depth = because_count + therefore_count
        
        if reasoning_depth >= 3:
            return f"Strong causal reasoning detected ({reasoning_depth} logical connections). You're not just collecting facts but building understanding - this depth of analysis positions you to make non-obvious connections."
        
        return ""
    
    def _identify_critical_gaps(self, content: str) -> str:
        """Identify what's missing that could unlock new insights"""
        
        # Implementation gap
        if "idea" in content or "concept" in content:
            if not any(word in content for word in ["test", "experiment", "pilot", "prototype", "try"]):
                return "Gap identified: Rich ideas without experimentation plans. Even the best concepts need reality contact - what's the smallest test that could validate or invalidate your thinking?"
        
        # Stakeholder gap
        if any(word in content for word in ["project", "initiative", "product", "solution"]):
            if not any(word in content for word in ["user", "customer", "stakeholder", "audience"]):
                return "Missing perspective: No explicit user/stakeholder consideration detected. The best solutions deeply understand who they serve - whose problem are you really solving?"
        
        # Metrics gap
        if any(word in content for word in ["goal", "objective", "success", "achieve"]):
            if not any(word in content for word in ["measure", "metric", "kpi", "indicator", "track"]):
                return "Insight gap: Goals without metrics often drift. What specific, observable changes would indicate you're succeeding? Defining measures sharpens thinking and accelerates learning."
        
        # Systems gap
        if content.count("problem") > 2 or content.count("issue") > 2:
            if not any(word in content for word in ["system", "cause", "root", "underlying", "pattern"]):
                return "Depth opportunity: Multiple problems might share systemic roots. Stepping back to see the system often reveals elegant interventions that address multiple issues simultaneously."
        
        return ""
    
    def _extract_content_themes(self, content: str) -> List[str]:
        """Extract meaningful themes from user content"""
        content_lower = content.lower()
        themes = []
        
        if "strategy" in content_lower or "plan" in content_lower:
            themes.append("strategic_planning")
        if "team" in content_lower or "people" in content_lower:
            themes.append("team_management")
        if "market" in content_lower or "customer" in content_lower:
            themes.append("market_focus")
        if "product" in content_lower or "feature" in content_lower:
            themes.append("product_development")
        if "goal" in content_lower or "objective" in content_lower:
            themes.append("goal_setting")
        
        return themes
    
    def _store_reflection_artifact(
        self,
        request: ReflectionComputationRequest,
        reflection: Dict[str, Any],
        substrate_ids: List[str],
        window_bounds: Tuple[Optional[str], Optional[str]],
    ) -> Optional[str]:
        """Persist reflection artifact using the available write paths."""

        payload_text = (reflection.get("text") or "").strip()
        if not payload_text:
            return None

        ws_id = str(request.workspace_id)
        b_id = str(request.basket_id)
        normalized_ids = [sid for sid in substrate_ids if sid]

        meta_payload = dict(reflection.get("meta") or {})
        meta_payload.setdefault("engine", "p3_llm_v2")
        if "generated_at" not in meta_payload:
            meta_payload["generated_at"] = datetime.utcnow().isoformat()

        window_start, window_end = window_bounds
        window_meta = meta_payload.get("window") or {}
        if window_start and not window_meta.get("start"):
            window_meta["start"] = window_start
        if window_end and not window_meta.get("end"):
            window_meta["end"] = window_end
        if window_meta:
            meta_payload["window"] = window_meta

        hash_key = reflection.get("hash_key") or self._make_hash_key(
            meta_payload.get("type", "reflection"),
            meta_payload.get("headline", ""),
            meta_payload.get("body", payload_text),
            normalized_ids,
        )
        hash_components = normalized_ids + ([hash_key] if hash_key else [])
        hash_input = "|".join(hash_components) if hash_components else b_id
        substrate_hash = f"substrate_{hashlib.sha256(hash_input.encode('utf-8')).hexdigest()}"

        # Attempt canonical RPC (new signature) first
        try:
            rpc_ids = normalized_ids.copy()
            if hash_key:
                try:
                    synthetic = UUID(hashlib.sha256(hash_key.encode('utf-8')).hexdigest()[:32])
                    rpc_ids.append(str(synthetic))
                except Exception:
                    pass
            resp = supabase.rpc(
                'fn_reflection_create_from_substrate',
                {
                    'p_basket_id': b_id,
                    'p_substrate_ids': rpc_ids,
                    'p_reflection_text': payload_text,
                    'p_computation_method': 'canon_window_analysis'
                }
            ).execute()
            if getattr(resp, 'data', None):
                reflection_id = resp.data
                try:
                    supabase.table('reflections_artifact').update({
                        'meta': meta_payload,
                        'substrate_window_start': window_start,
                        'substrate_window_end': window_end,
                        'substrate_hash': substrate_hash,
                    }).eq('id', reflection_id).execute()
                except Exception as inner:
                    self.logger.debug(f"Failed to update reflection metadata after RPC insert: {inner}")
                self.logger.info("Canon P3: stored via RPC (new signature)")
                return reflection_id
        except Exception as e:
            self.logger.debug(f"RPC (new signature) failed: {e}")

        # Legacy RPC compatibility
        try:
            resp2 = supabase.rpc(
                'fn_reflection_create_from_substrate',
                {'p_basket_id': b_id, 'p_reflection_text': payload_text}
            ).execute()
            if getattr(resp2, 'data', None):
                reflection_id = resp2.data
                try:
                    supabase.table('reflections_artifact').update({
                        'meta': meta_payload,
                        'substrate_window_start': window_start,
                        'substrate_window_end': window_end,
                        'substrate_hash': substrate_hash,
                    }).eq('id', reflection_id).execute()
                except Exception as inner:
                    self.logger.debug(f"Failed to update reflection metadata after legacy RPC insert: {inner}")
                self.logger.info("Canon P3: stored via RPC (legacy signature)")
                return reflection_id
        except Exception as e:
            self.logger.debug(f"RPC (legacy signature) failed: {e}")

        # Direct insert fallback with conflict-aware update
        try:
            minimal = {
                "workspace_id": ws_id,
                "basket_id": b_id,
                "reflection_text": payload_text,
                "reflection_target_type": "substrate",
                "computation_timestamp": datetime.utcnow().isoformat(),
                "substrate_hash": substrate_hash,
                "substrate_window_start": window_start,
                "substrate_window_end": window_end,
                "meta": meta_payload,
            }
            insert_resp = supabase.table('reflections_artifact').insert(minimal).execute()
            inserted_id = None
            if getattr(insert_resp, 'data', None):
                first_row = insert_resp.data[0] if isinstance(insert_resp.data, list) and insert_resp.data else None
                if first_row and isinstance(first_row, dict):
                    inserted_id = first_row.get('id')
            self.logger.info("Canon P3: stored via direct minimal insert")
            return inserted_id
        except Exception as e:
            msg = str(e)
            if '23505' in msg or 'duplicate key value violates unique constraint' in msg:
                update_resp = supabase.table('reflections_artifact').update({
                    'reflection_text': payload_text,
                    'meta': meta_payload,
                    'substrate_window_start': window_start,
                    'substrate_window_end': window_end,
                    'computation_timestamp': datetime.utcnow().isoformat(),
                }).eq('basket_id', b_id).eq('substrate_hash', substrate_hash).execute()
                updated_id = None
                if getattr(update_resp, 'data', None):
                    first_row = update_resp.data[0] if isinstance(update_resp.data, list) and update_resp.data else None
                    if first_row and isinstance(first_row, dict):
                        updated_id = first_row.get('id')
                self.logger.info("Canon P3: reflection already exists (idempotent)")
                return updated_id
            self.logger.error(f"Failed to store reflection artifact (fallback): {e}")
            raise
