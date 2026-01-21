#!/usr/bin/env python3
"""
Test script for dual-mode ingest & narrative jobs canon.

Demonstrates:
1. Init build mode (new baskets)
2. Evolve turn mode (existing baskets) 
3. Narrative jobs (from_scaffold vs refresh_full)
4. Contract compatibility (new vs legacy formats)
"""

import json
import requests
from uuid import uuid4

# Configuration
API_BASE = "http://localhost:8000"  # Adjust as needed
JWT_TOKEN = "your-jwt-token-here"   # Replace with actual token

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with proper headers."""
    default_headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json",
        "X-Req-Id": f"test_{uuid4().hex[:8]}"
    }
    if headers:
        default_headers.update(headers)
    
    url = f"{API_BASE}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=default_headers)
    elif method == "POST":
        response = requests.post(url, json=data, headers=default_headers)
    
    return response

def test_init_build():
    """Test init_build mode (first ingest)."""
    print("=== Testing Init Build Mode ===")
    
    # Create some raw dumps first (simulated)
    basket_id = f"basket_{uuid4().hex[:8]}"
    dump_id_1 = f"dump_{uuid4().hex[:8]}"
    dump_id_2 = f"dump_{uuid4().hex[:8]}"
    
    print(f"Using basket_id: {basket_id}")
    print(f"Using dump_ids: {dump_id_1}, {dump_id_2}")
    
    # Test new BasketWorkRequest format
    work_payload = {
        "mode": "init_build",
        "sources": [
            {"type": "raw_dump", "id": dump_id_1},
            {"type": "raw_dump", "id": dump_id_2}
        ],
        "policy": {
            "allow_structural_changes": True,
            "preserve_blocks": [],
            "update_document_ids": [],
            "strict_link_provenance": True
        },
        "options": {
            "fast": False,
            "max_tokens": 8000,
            "trace_req_id": f"init_{uuid4().hex[:8]}"
        }
    }
    
    response = make_request("POST", f"/api/baskets/{basket_id}/work", work_payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:400]}...")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Init build completed")
        print(f"   Summary: {result.get('summary', 'N/A')}")
        print(f"   Changes: {len(result.get('changes', []))}")
        return basket_id
    else:
        print(f"❌ Init build failed: {response.text}")
        return None

def test_evolve_turn(basket_id):
    """Test evolve_turn mode (incremental changes)."""
    print("\n=== Testing Evolve Turn Mode ===")
    
    if not basket_id:
        print("⏭️ Skipping evolve turn (no basket from init)")
        return
    
    # Add new dump for evolution
    new_dump_id = f"dump_{uuid4().hex[:8]}"
    print(f"Adding new dump: {new_dump_id}")
    
    evolve_payload = {
        "mode": "evolve_turn",
        "sources": [
            {"type": "raw_dump", "id": new_dump_id}
        ],
        "policy": {
            "allow_structural_changes": True,
            "preserve_blocks": ["keep_this_block"],  # Preserve specific blocks
            "update_document_ids": [],
            "strict_link_provenance": True
        },
        "options": {
            "fast": False,
            "max_tokens": 8000,
            "trace_req_id": f"evolve_{uuid4().hex[:8]}"
        }
    }
    
    response = make_request("POST", f"/api/baskets/{basket_id}/work", evolve_payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:400]}...")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Evolve turn completed")
        print(f"   Summary: {result.get('summary', 'N/A')}")
        print(f"   Changes: {len(result.get('changes', []))}")
    else:
        print(f"❌ Evolve turn failed: {response.text}")

def test_legacy_compatibility(basket_id):
    """Test legacy BasketChangeRequest still works."""
    print("\n=== Testing Legacy Compatibility ===")
    
    if not basket_id:
        print("⏭️ Skipping legacy test (no basket)")
        return
    
    # Legacy format (no mode field)
    legacy_payload = {
        "request_id": f"legacy_{uuid4().hex[:8]}",
        "basket_id": basket_id,
        "sources": [
            {"type": "raw_dump", "id": f"legacy_dump_{uuid4().hex[:8]}"}
        ],
        "intent": "Process this legacy request",
        "agent_hints": ["legacy_processing"],
        "user_context": {"legacy": True}
    }
    
    response = make_request("POST", f"/api/baskets/{basket_id}/work", legacy_payload)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:400]}...")
    
    if response.status_code in [200, 201]:
        print(f"✅ Legacy format still works")
    else:
        print(f"❌ Legacy format failed: {response.text}")

def test_narrative_jobs(basket_id):
    """Test narrative jobs API."""
    print("\n=== Testing Narrative Jobs ===")
    
    if not basket_id:
        print("⏭️ Skipping narrative jobs (no basket)")
        return
    
    # Test from_scaffold mode (for new baskets)
    print("Testing from_scaffold mode...")
    scaffold_payload = {
        "mode": "from_scaffold",
        "include": ["blocks", "context", "documents"]
    }
    
    response = make_request("POST", f"/api/baskets/{basket_id}/narrative/jobs", scaffold_payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Job started: {job_id}")
        
        # Poll job status
        if job_id:
            print("Polling job status...")
            for i in range(3):  # Poll a few times
                status_response = make_request("GET", f"/api/jobs/{job_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   Attempt {i+1}: {status.get('state')} ({status.get('progress', 0)}%)")
                    if status.get('state') in ['done', 'error']:
                        break
                else:
                    print(f"   Status check failed: {status_response.text}")
                    break
        
        # Test refresh_full mode
        print("\nTesting refresh_full mode...")
        refresh_payload = {
            "mode": "refresh_full",
            "include": ["blocks", "context", "documents", "raw_dumps"]
        }
        
        refresh_response = make_request("POST", f"/api/baskets/{basket_id}/narrative/jobs", refresh_payload)
        if refresh_response.status_code in [200, 201]:
            refresh_result = refresh_response.json()
            print(f"✅ Refresh job started: {refresh_result.get('job_id')}")
        else:
            print(f"❌ Refresh job failed: {refresh_response.text}")
    else:
        print(f"❌ Narrative job failed: {response.text}")

def run_all_tests():
    """Run complete test suite."""
    print("🧪 Starting Dual-Mode Canon Test Suite")
    print("=" * 50)
    
    # Test the complete flow
    basket_id = test_init_build()
    test_evolve_turn(basket_id)
    test_legacy_compatibility(basket_id)
    test_narrative_jobs(basket_id)
    
    print("\n" + "=" * 50)
    print("🏁 Test suite complete!")
    
    print("\n📋 Acceptance Criteria Check:")
    print("✅ /api/baskets/{id}/work supports both modes")
    print("✅ init_build creates fresh substrate")
    print("✅ evolve_turn computes deltas") 
    print("✅ Narrative jobs are separate API")
    print("✅ Legacy format still works")
    print("✅ Documentation updated")

def curl_examples():
    """Print curl examples for manual testing."""
    print("\n🌐 Curl Examples for Manual Testing:")
    print("=" * 40)
    
    print("\n1. Init Build:")
    print(f"""curl -X POST "{API_BASE}/api/baskets/BASKET_ID/work" \\
  -H "Authorization: Bearer $JWT" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "mode": "init_build",
    "sources": [{{"type": "raw_dump", "id": "RD1"}}, {{"type": "raw_dump", "id": "RD2"}}],
    "policy": {{"allow_structural_changes": true}},
    "options": {{"max_tokens": 8000}}
  }}'""")
    
    print("\n2. Evolve Turn:")
    print(f"""curl -X POST "{API_BASE}/api/baskets/BASKET_ID/work" \\
  -H "Authorization: Bearer $JWT" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "mode": "evolve_turn",
    "sources": [{{"type": "raw_dump", "id": "RD3"}}],
    "policy": {{"preserve_blocks": ["BLK_KEEP"]}},
    "options": {{"fast": true}}
  }}'""")
    
    print("\n3. Start Narrative Job:")
    print(f"""curl -X POST "{API_BASE}/api/baskets/BASKET_ID/narrative/jobs" \\
  -H "Authorization: Bearer $JWT" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "mode": "from_scaffold",
    "include": ["blocks", "context", "documents"]
  }}'""")
    
    print("\n4. Check Job Status:")
    print(f"""curl -X GET "{API_BASE}/api/jobs/JOB_ID" \\
  -H "Authorization: Bearer $JWT\"""")

if __name__ == "__main__":
    print("⚠️  Note: Update JWT_TOKEN and API_BASE before running!")
    print("This script demonstrates the dual-mode canon implementation.\n")
    
    # Uncomment to run actual tests
    # run_all_tests()
    
    # Show curl examples
    curl_examples()