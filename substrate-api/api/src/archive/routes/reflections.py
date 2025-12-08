from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from infra.utils.supabase_client import supabase_admin_client as supabase
from app.agents.pipeline.reflection_agent_canon_v2 import CanonP3ReflectionAgent
from app.agents.pipeline.reflection_agent_canon_v2 import ReflectionComputationRequest

router = APIRouter(prefix="/api/reflections", tags=["reflections"])

class ComputeWindowBody(BaseModel):
    workspace_id: str
    basket_id: Optional[str] = None
    agent_id: Optional[str] = "p3_reflection_agent"
    substrate_window_hours: Optional[int] = None
    document_focus: Optional[str] = None
    proposal_focus: Optional[str] = None

@router.post("/compute_window")
async def compute_window(body: ComputeWindowBody):
    try:
        # Handle document-specific reflections
        if body.document_focus:
            return await compute_document_reflection(body.document_focus, body.workspace_id)
        
        # Handle proposal-specific reflections  
        if body.proposal_focus:
            # For now, fall back to general basket analysis with proposal context
            # TODO: Implement dedicated proposal analysis
            pass
        
        # Standard basket-level reflection
        agent = CanonP3ReflectionAgent()
        req = ReflectionComputationRequest(
            workspace_id=body.workspace_id,
            basket_id=body.basket_id,
            agent_id=body.agent_id or "p3_reflection_agent",
        )
        
        # Pass time window constraint to agent if specified
        if body.substrate_window_hours:
            req.substrate_window_hours = body.substrate_window_hours
            
        result = await agent.compute_reflections(req)
        return {"success": True, "result": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reflection compute failed: {e}")

class ComputeEventBody(BaseModel):
    workspace_id: str
    event_id: str

@router.post("/compute_event")
async def compute_event(body: ComputeEventBody):
    try:
        ev = supabase.table("events").select("id,basket_id,workspace_id,kind,payload").eq("id", body.event_id).single().execute()
        if not ev.data:
            raise HTTPException(status_code=404, detail="event_not_found")

        basket_id = ev.data["basket_id"]
        kind = ev.data["kind"]
        payload = ev.data.get("payload", {})
        subject = payload.get("block_id") or payload.get("document_id") or payload.get("relationship_id") or "this update"
        text = f"Insight: Event '{kind}' occurred for {subject}. This reflection summarizes its potential impact and suggests next steps."

        resp = supabase.rpc('fn_reflection_create_from_substrate', {
            'p_basket_id': basket_id,
            'p_reflection_text': text,
        }).execute()
        reflection_id = resp.data

        return {"success": True, "reflection_id": reflection_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event reflection failed: {e}")

@router.post("/documents/{document_id}/compute")
async def compute_document_reflection(document_id: str, workspace_id: str):
    try:
        doc = supabase.table("documents").select("id,basket_id,workspace_id,content_raw").eq("id", document_id).single().execute()
        if not doc.data:
            raise HTTPException(status_code=404, detail="document_not_found")
        if doc.data["workspace_id"] != workspace_id:
            raise HTTPException(status_code=403, detail="forbidden")
        content = (doc.data.get("content_raw") or "").strip()
        text = (
            "Not enough content in this document to compute a detailed reflection yet. Consider adding more structured sections or references."
            if len(content) < 200
            else f"Document reflection for {document_id}. Summary based on {len(content)} characters of current content."
        )
        resp = supabase.rpc('fn_reflection_create_from_document', {
            'p_basket_id': doc.data['basket_id'],
            'p_document_id': document_id,
            'p_reflection_text': text,
        }).execute()
        return {"success": True, "reflection_id": resp.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document reflection failed: {e}")

@router.get("/documents/{document_id}")
async def list_document_reflections(document_id: str, workspace_id: str, cursor: Optional[str] = None, limit: int = 10):
    try:
        query = (
            supabase
            .table('reflections_artifact')
            .select('*')
            .eq('workspace_id', workspace_id)
            .eq('reflection_target_type', 'document')
            .eq('reflection_target_id', document_id)
            .order('computation_timestamp', desc=True)
            .limit(limit + 1)
        )
        if cursor:
            query = query.lt('computation_timestamp', cursor)
        res = query.execute()
        rows = res.data or []
        has_more = len(rows) > limit
        results = rows[:limit]
        next_cursor = results[-1]['computation_timestamp'] if has_more else None
        return {"reflections": results, "has_more": has_more, "next_cursor": next_cursor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List document reflections failed: {e}")


@router.get("/baskets/{basket_id}")
async def list_basket_reflections(basket_id: str, workspace_id: str, cursor: Optional[str] = None, limit: int = 10, refresh: bool = False):
    try:
        if refresh:
            # Optionally trigger compute on refresh signal
            agent = CanonP3ReflectionAgent()
            req = ReflectionComputationRequest(workspace_id=workspace_id, basket_id=basket_id, agent_id="p3_reflection_agent")
            try:
                await agent.compute_reflections(req)
            except Exception:
                # Non-fatal
                pass
        query = (
            supabase
            .table('reflections_artifact')
            .select('*')
            .eq('workspace_id', workspace_id)
            .eq('basket_id', basket_id)
            .order('computation_timestamp', desc=True)
            .limit(limit + 1)
        )
        if cursor:
            query = query.lt('computation_timestamp', cursor)
        res = query.execute()
        rows = res.data or []
        has_more = len(rows) > limit
        results = rows[:limit]
        next_cursor = results[-1]['computation_timestamp'] if has_more else None
        return {"reflections": results, "has_more": has_more, "next_cursor": next_cursor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List basket reflections failed: {e}")
