"""Tests for PDF ingestion functionality."""

import os
import json
from uuid import uuid4
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock environment variables before imports
BASE = "https://test.supabase.co"
os.environ["ALLOWED_PUBLIC_BASE"] = f"{BASE}/storage/v1/object/public/"
os.environ["PDF_MAX_BYTES"] = "1000000"
os.environ["CHUNK_LEN"] = "1000"

from src.app.main import app
from src.app.routes.dump_new import router


class TestPDFIngestion:
    """Test PDF parsing and ingestion."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock auth headers."""
        return {
            "Authorization": "Bearer test-token",
            "X-Req-Id": "test-123"
        }
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        with patch("src.app.routes.dump_new.supabase") as mock:
            # Mock table operations
            mock.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "test-dump-id"}],
                error=None
            )
            yield mock
    
    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT verification."""
        with patch("src.app.routes.dump_new.verify_jwt") as mock:
            mock.return_value = {"user_id": "test-user"}
            yield mock
    
    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx for PDF fetching."""
        with patch("src.app.routes.dump_new.httpx.AsyncClient") as mock:
            client_instance = MagicMock()
            mock.return_value.__aenter__.return_value = client_instance
            
            # Mock PDF response
            response = MagicMock()
            response.raise_for_status = MagicMock()
            response.headers = {"Content-Type": "application/pdf", "Content-Length": "50000"}
            response.content = b"%PDF-1.4\n%Test PDF content\nThis is extracted text from PDF."
            
            client_instance.get.return_value = response
            yield mock
    
    @pytest.fixture
    def mock_pdf_extract(self):
        """Mock PDF text extraction."""
        with patch("src.app.routes.dump_new.extract_pdf_text") as mock:
            mock.return_value = "This is extracted text from the PDF document."
            yield mock
    
    async def test_pdf_ingestion_success(
        self, client, auth_headers, mock_supabase, mock_jwt, mock_httpx, mock_pdf_extract
    ):
        """Test successful PDF ingestion."""
        payload = {
            "basket_id": str(uuid4()),
            "dump_request_id": str(uuid4()),
            "text_dump": "User provided text",
            "file_url": f"{BASE}/storage/v1/object/public/docs/test.pdf"
        }
        
        response = client.post("/dumps/new", json=payload, headers=auth_headers)
        
        assert response.status_code == 201
        result = response.json()
        assert "dump_id" in result
        
        # Verify PDF was fetched
        mock_httpx.assert_called_once()
        
        # Verify text was extracted
        mock_pdf_extract.assert_called_once()
        
        # Verify dump was created with metadata
        insert_call = mock_supabase.table.return_value.insert.call_args[0][0]
        parsed_insert = json.loads(insert_call)
        assert parsed_insert["basket_id"] == payload["basket_id"]
        assert "source_meta" in parsed_insert
        assert parsed_insert["ingest_trace_id"] == "test-123"
    
    async def test_disallowed_url(self, client, auth_headers, mock_jwt):
        """Test SSRF protection blocks disallowed URLs."""
        payload = {
            "basket_id": str(uuid4()),
            "dump_request_id": str(uuid4()),
            "text_dump": "",
            "file_url": "https://evil.com/malicious.pdf"
        }
        
        response = client.post("/dumps/new", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Disallowed file URL" in response.text
    
    async def test_oversized_pdf(self, client, auth_headers, mock_jwt, mock_httpx):
        """Test rejection of oversized PDFs."""
        # Mock oversized response
        response_mock = MagicMock()
        response_mock.headers = {"Content-Length": "2000000"}  # 2MB > 1MB limit
        
        client_instance = MagicMock()
        client_instance.get.return_value = response_mock
        mock_httpx.return_value.__aenter__.return_value = client_instance
        
        payload = {
            "basket_id": str(uuid4()),
            "dump_request_id": str(uuid4()),
            "text_dump": "",
            "file_url": f"{BASE}/storage/v1/object/public/big.pdf"
        }
        
        response = client.post("/dumps/new", json=payload, headers=auth_headers)
        
        assert response.status_code == 413
        assert "File too large" in response.text
    
    async def test_no_usable_text(self, client, auth_headers, mock_jwt):
        """Test error when no usable text provided."""
        payload = {
            "basket_id": str(uuid4()),
            "dump_request_id": str(uuid4()),
            "text_dump": ""
        }
        
        response = client.post("/dumps/new", json=payload, headers=auth_headers)
        
        assert response.status_code == 422
        assert "No content provided" in response.text
    
    async def test_idempotency(self, client, auth_headers, mock_jwt, mock_supabase):
        """Test idempotent dump creation."""
        # Mock existing dump check
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "existing-dump-id"}]
        )
        
        payload = {
            "basket_id": str(uuid4()),
            "dump_request_id": str(uuid4()),
            "text_dump": "Test content"
        }
        
        # First request
        response1 = client.post("/dumps/new", json=payload, headers=auth_headers)
        assert response1.status_code == 201
        
        # Second request with same trace ID should return cached result
        response2 = client.post("/dumps/new", json=payload, headers=auth_headers)
        assert response2.status_code == 201
        
        # Should return same dump ID
        assert response1.json() == response2.json()


class TestWorkRoute:
    """Test basket work route with real entities."""
    
    @pytest.fixture
    def mock_canonical_processor(self):
        """Mock canonical queue processor to return real-looking entities."""
        with patch("src.app.routes.baskets.CanonicalQueueProcessor") as processor_cls:
            processor = MagicMock()
            processor.process_basket_work.return_value = {
                "delta_id": str(uuid4()),
                "basket_id": "test-basket",
                "summary": "Created 3 blocks from 1 source",
                "changes": [
                    {
                        "entity": "context_block",
                        "id": str(uuid4()),
                        "from_version": None,
                        "to_version": 1,
                        "diff": "Created from raw dump RD1"
                    }
                ],
                "confidence": 0.9,
                "created_at": "2024-01-01T00:00:00Z"
            }
            processor.process_basket_change.return_value = processor.process_basket_work.return_value
            processor_cls.return_value = processor
            yield processor
    
    async def test_init_build_mode(self, client, auth_headers, mock_jwt, mock_canonical_processor):
        """Test init_build mode returns real entities."""
        payload = {
            "mode": "init_build",
            "sources": [{"type": "raw_dump", "id": "RD1"}],
            "options": {"trace_req_id": "test-init-001"}
        }
        
        response = client.post("/api/baskets/test-basket/work", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify real entity IDs returned
        assert len(result["changes"]) > 0
        assert result["changes"][0]["id"] != "block_RD1_0"  # Not synthetic
        assert result["changes"][0]["entity"] == "context_block"
        assert result["changes"][0]["to_version"] == 1
    
    async def test_evolve_turn_mode(self, client, auth_headers, mock_jwt, mock_canonical_processor):
        """Test evolve_turn mode with version updates."""
        mock_canonical_processor.process_basket_work.return_value["changes"] = [
            {
                "entity": "context_block", 
                "id": "existing-block-id",
                "from_version": 1,
                "to_version": 2,
                "diff": "Updated via evolve turn"
            }
        ]
        
        payload = {
            "mode": "evolve_turn",
            "sources": [{"type": "raw_dump", "id": "RD2"}],
            "policy": {"preserve_blocks": ["keep-this-one"]}
        }
        
        response = client.post("/api/baskets/test-basket/work", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify version update
        assert result["changes"][0]["from_version"] == 1
        assert result["changes"][0]["to_version"] == 2
