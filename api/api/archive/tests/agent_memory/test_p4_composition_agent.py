import os
import sys
import types

import pytest

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role")


class _StubSupabaseClient:
    def __init__(self):
        self.postgrest = types.SimpleNamespace(auth=lambda *_args, **_kwargs: None)

    def table(self, *_args, **_kwargs):  # pragma: no cover - not exercised in tests
        raise NotImplementedError("Supabase table access should be mocked in unit tests")


_supabase_module = types.ModuleType("supabase")
_supabase_module.create_client = lambda *_args, **_kwargs: _StubSupabaseClient()
_supabase_module.Client = _StubSupabaseClient
sys.modules["supabase"] = _supabase_module


from app.agents.pipeline.composition_agent import CompositionRequest, P4CompositionAgent

from infra.substrate.services.llm import LLMResponse


class _StubLLM:
    """Simple stub provider for deterministic P4 composition tests."""

    def __init__(self, *, text_responses=None, json_responses=None):
        self._text_responses = list(text_responses or [])
        self._json_responses = list(json_responses or [])


    async def get_text_response(self, *_args, **_kwargs):
        if not self._text_responses:
            raise AssertionError("Unexpected additional text response request")
        return self._text_responses.pop(0)

    async def get_json_response(self, *_args, **_kwargs):
        if not self._json_responses:
            raise AssertionError("JSON response path should not be invoked in this test")
        return self._json_responses.pop(0)

@pytest.mark.asyncio
async def test_generate_section_content_success(monkeypatch):
    stub_llm = _StubLLM(
        text_responses=[
            LLMResponse(success=True, content="  Generated narrative  ", parsed=None, usage=None, error=None)
        ]
    )
    monkeypatch.setattr("app.agents.pipeline.composition_agent.get_llm", lambda: stub_llm)

    agent = P4CompositionAgent()

    section = {
        "title": "Connected Impact",
        "content": "Discuss how updates influenced downstream work",
        "substrate_refs": ["block"],
        "relationship_focus": "causal chains"
    }
    selected_substrate = [
        {"type": "block", "content": "Upstream change triggered new data flows"},
        {"type": "dump", "content": "Additional raw context that should be ignored"},
    ]
    narrative = {"summary": "Integration summary", "synthesis_approach": "Connect"}

    result = await agent._generate_section_content(section, selected_substrate, narrative)

    assert result == "Generated narrative"


@pytest.mark.asyncio
async def test_generate_section_content_failure_falls_back_to_outline(monkeypatch):
    stub_llm = _StubLLM(
        text_responses=[LLMResponse(success=False, content="", parsed=None, usage=None, error="rate limit")]
    )
    monkeypatch.setattr("app.agents.pipeline.composition_agent.get_llm", lambda: stub_llm)

    agent = P4CompositionAgent()

    section = {
        "title": "Relationship Mapping",
        "content": "Outline relationships when generation fails",
        "substrate_refs": [],
    }
    selected_substrate = [
        {"type": "context_item", "content": "Entity details"},
    ]
    narrative = {"summary": "Failure summary", "synthesis_approach": "Fallback"}

    result = await agent._generate_section_content(section, selected_substrate, narrative)

    assert result == section["content"]


@pytest.mark.asyncio
async def test_score_and_select_falls_back_when_json_call_fails(monkeypatch):
    stub_llm = _StubLLM(
        json_responses=[
            LLMResponse(
                success=False,
                content="",
                parsed=None,
                usage=None,
                error="Invalid schema for response_format",
            )
        ]
    )
    monkeypatch.setattr("app.agents.pipeline.composition_agent.get_llm", lambda: stub_llm)

    agent = P4CompositionAgent()

    candidates = [
        {
            "type": "block",
            "content": "Older, lower confidence entry",
            "confidence_score": 0.2,
            "created_at": "2025-09-18T10:00:00",
        },
        {
            "type": "block",
            "content": "Recent high confidence insight",
            "confidence_score": 0.9,
            "created_at": "2025-09-20T15:30:00",
        },
    ]

    request = CompositionRequest(
        document_id="doc-1",
        basket_id="basket-1",
        workspace_id="ws-1",
        intent="Summarize updates",
    )

    strategy = {"document_type": "summary", "key_themes": ["updates"]}

    selected = await agent._score_and_select(candidates, request, strategy)

    assert selected, "Fallback selection should return candidates"
    assert selected[0]["content"] == "Recent high confidence insight"
    assert "fallback" in selected[0]["selection_reason"].lower()