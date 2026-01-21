#!/usr/bin/env python3
"""
Test script for composition_agent_v2.py
Verifies the agent can query blocks correctly before deployment
"""
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra.utils.supabase_client import supabase_admin_client as supabase

def test_blocks_query():
    """Test if blocks query works with correct status values"""

    basket_id = "019ca0bd-87b5-4153-86e2-e63f2309ecb2"
    window_days = 90
    recency_cutoff = datetime.utcnow() - timedelta(days=window_days)

    print(f"Testing blocks query for basket: {basket_id}")
    print(f"Recency cutoff: {recency_cutoff.isoformat()}")

    # Test with uppercase (old, broken)
    print("\n1. Testing with UPPERCASE status values (should fail)...")
    try:
        blocks_query = (
            supabase.table("blocks")
            .select("*")
            .eq("basket_id", basket_id)
            .gte("created_at", recency_cutoff.isoformat())
            .in_("status", ["ACCEPTED", "LOCKED"])
            .order("created_at", desc=True)
            .limit(20)
        )
        result = blocks_query.execute()
        print(f"   ❌ Found {len(result.data)} blocks (should be 0)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test with lowercase (new, fixed)
    print("\n2. Testing with lowercase status values (should work)...")
    try:
        blocks_query = (
            supabase.table("blocks")
            .select("*")
            .eq("basket_id", basket_id)
            .gte("created_at", recency_cutoff.isoformat())
            .in_("status", ["accepted", "locked"])
            .order("created_at", desc=True)
            .limit(20)
        )
        result = blocks_query.execute()
        print(f"   ✅ Found {len(result.data)} blocks")

        if result.data:
            print(f"\n   Sample block:")
            print(f"   - ID: {result.data[0]['id']}")
            print(f"   - Status: {result.data[0]['status']}")
            print(f"   - Created: {result.data[0]['created_at']}")
            print(f"   - Content preview: {result.data[0].get('content', '')[:100]}...")

        return len(result.data) > 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_blocks_query()
    sys.exit(0 if success else 1)
