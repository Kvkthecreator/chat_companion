import json
from unittest.mock import patch, MagicMock
import pytest

from app.services.llm import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_json_response_parses_valid_json():
    provider = OpenAIProvider()

    with patch.object(provider.client.chat.completions, 'create') as mock_create:
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({"ok": True, "items": [1,2,3]})
        mock_resp.choices = [mock_choice]
        mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
        mock_create.return_value = mock_resp

        res = await provider.get_json_response("return valid json", schema_name=None)
        assert res.success is True
        assert res.parsed == {"ok": True, "items": [1,2,3]}
        assert res.usage["input_tokens"] == 10
        assert res.usage["output_tokens"] == 5


@pytest.mark.asyncio
async def test_openai_provider_json_response_extracts_embedded_json():
    provider = OpenAIProvider()

    with patch.object(provider.client.chat.completions, 'create') as mock_create:
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Some preface {\"x\": 1} trailing"
        mock_resp.choices = [mock_choice]
        mock_resp.usage = None
        mock_create.return_value = mock_resp

        res = await provider.get_json_response("return json")
        assert res.success is True
        assert res.parsed == {"x": 1}


@pytest.mark.asyncio
async def test_openai_provider_text_response_returns_text():
    provider = OpenAIProvider()

    with patch.object(provider.client.chat.completions, 'create') as mock_create:
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello world"
        mock_resp.choices = [mock_choice]
        mock_resp.usage = MagicMock(prompt_tokens=7, completion_tokens=2)
        mock_create.return_value = mock_resp

        res = await provider.get_text_response("hi")
        assert res.success is True
        assert res.content == "Hello world"
        assert res.parsed is None
