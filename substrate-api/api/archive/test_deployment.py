#!/usr/bin/env python3
"""
Test script to verify backend deployment is working properly.

Run this after deployment to verify:
1. Database connection works
2. Tables exist
3. Basic API endpoints respond
4. Manager Agent system functions

Usage:
    python test_deployment.py [BASE_URL]
    
    BASE_URL defaults to http://localhost:8000
    For Render: python test_deployment.py https://your-app.onrender.com
"""

import asyncio
import sys
import json
import httpx
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_database_connection():
    """Test database connection via health endpoint."""
    print("🔌 Testing database connection...")
    
    try:
        from src.app.deps import get_db
        db = await get_db()
        result = await db.fetch_one("SELECT 1 as test")
        print(f"  ✓ Database connection successful: {result}")
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False


async def test_tables_exist():
    """Test that required tables exist."""
    print("🗂️  Testing table existence...")
    
    tables_to_check = [
        "idempotency_keys",
        "basket_deltas", 
        "events"  # Migrated from basket_events
    ]
    
    try:
        from src.app.deps import get_db
        db = await get_db()
        
        for table in tables_to_check:
            try:
                result = await db.fetch_one(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    ) as exists
                """)
                if result["exists"]:
                    print(f"  ✓ Table {table} exists")
                else:
                    print(f"  ✗ Table {table} missing")
                    return False
            except Exception as e:
                print(f"  ✗ Failed to check table {table}: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to connect to database: {e}")
        return False


async def test_api_endpoints(base_url: str = "http://localhost:8000"):
    """Test API endpoints."""
    print(f"🌐 Testing API endpoints at {base_url}...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test basic health
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("  ✓ Basic health endpoint works")
            else:
                print(f"  ✗ Basic health failed: {response.status_code}")
                return False
            
            # Test database health
            response = await client.get(f"{base_url}/health/db")
            if response.status_code == 200:
                result = response.json()
                if result.get("database_connected"):
                    print("  ✓ Database health endpoint works")
                else:
                    print(f"  ✗ Database health shows disconnected: {result}")
                    return False
            else:
                print(f"  ✗ Database health failed: {response.status_code}")
                return False
            
            # Test basket endpoint (should fail without auth, but shouldn't crash)
            response = await client.post(
                f"{base_url}/api/baskets/test-123/work",
                json={
                    "request_id": "test-req-001",
                    "basket_id": "test-123",
                    "intent": "test deployment",
                    "sources": [{"type": "text", "content": "test"}]
                }
            )
            
            # We expect this to fail due to auth, but not crash
            if response.status_code in [401, 403, 422]:
                print("  ✓ Basket endpoint responds (auth required as expected)")
            elif response.status_code == 500:
                print(f"  ⚠️  Basket endpoint returns 500: {response.text}")
                print("    This might indicate missing auth middleware or database issues")
            else:
                print(f"  ? Basket endpoint unexpected status: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ API test failed: {e}")
            return False


async def test_manager_system():
    """Test Manager Agent system components."""
    print("🤖 Testing Manager Agent system...")
    
    try:
        # Test idempotency service
        from infra.substrate.services.idempotency import already_processed, mark_processed
        from infra.substrate.services.deltas import persist_delta
        from infra.substrate.services.events import publish_event
        from contracts.basket import BasketDelta
        from src.app.deps import get_db
        
        db = await get_db()
        
        # Test idempotency
        test_request_id = "test-deployment-001"
        is_processed = await already_processed(db, test_request_id)
        print(f"  ✓ Idempotency check works: {is_processed}")
        
        # Test event publishing
        await publish_event(db, "test.deployment", {"message": "testing"})
        print("  ✓ Event publishing works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Manager system test failed: {e}")
        return False


async def main():
    """Run all tests."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🚀 Starting deployment verification tests...")
    print(f"Target: {base_url}")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_database_connection())
    results.append(await test_tables_exist())
    results.append(await test_api_endpoints(base_url))
    results.append(await test_manager_system())
    
    print("=" * 50)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ Backend deployment is working correctly!")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("🔧 Please check the errors above and fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())