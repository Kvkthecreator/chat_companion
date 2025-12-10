#!/usr/bin/env python3
"""
Seed demo data into Clearinghouse database.

This script:
1. Creates a demo workspace and catalog (if not exists)
2. Loads transformed track data via the bulk import API
3. Optionally triggers embedding generation

Usage:
    # Using API (requires auth token):
    python seed_demo_data.py --api-url https://your-api.onrender.com --token YOUR_JWT_TOKEN

    # Direct database (requires DATABASE_URL):
    python seed_demo_data.py --direct --database-url postgresql://...

Environment variables:
    API_URL - Clearinghouse API base URL
    API_TOKEN - JWT token for authentication
    DATABASE_URL - Direct database connection string
"""

import argparse
import json
import os
import sys
from pathlib import Path

# For API approach
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# For direct DB approach
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


DEMO_WORKSPACE = {
    "name": "Nova Entertainment Demo",
    "description": "Demo workspace for Clearinghouse sales presentations"
}

DEMO_CATALOG = {
    "name": "Nova K-Pop Catalog",
    "description": "50 tracks across 4 artists - K-pop, Ballad, OST",
    "content_types": ["sound_recording"],
    "metadata": {
        "label": "Nova Entertainment",
        "region": "Korea",
        "demo": True
    }
}


async def seed_via_api(api_url: str, token: str, data_file: Path):
    """Seed data using the Clearinghouse API."""
    if not HAS_HTTPX:
        print("Error: httpx not installed. Run: pip install httpx")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=api_url, headers=headers, timeout=60.0) as client:
        # 1. Check/create workspace
        print("Checking for existing workspace...")
        resp = await client.get("/api/v1/workspaces")
        resp.raise_for_status()
        workspaces = resp.json().get("workspaces", [])

        demo_ws = next((w for w in workspaces if w["name"] == DEMO_WORKSPACE["name"]), None)
        if demo_ws:
            workspace_id = demo_ws["id"]
            print(f"Using existing workspace: {workspace_id}")
        else:
            print("Creating demo workspace...")
            resp = await client.post("/api/v1/workspaces", json=DEMO_WORKSPACE)
            resp.raise_for_status()
            workspace_id = resp.json()["workspace"]["id"]
            print(f"Created workspace: {workspace_id}")

        # 2. Check/create catalog
        print("Checking for existing catalog...")
        resp = await client.get(f"/api/v1/workspaces/{workspace_id}/catalogs")
        resp.raise_for_status()
        catalogs = resp.json().get("catalogs", [])

        demo_cat = next((c for c in catalogs if c["name"] == DEMO_CATALOG["name"]), None)
        if demo_cat:
            catalog_id = demo_cat["id"]
            print(f"Using existing catalog: {catalog_id}")
        else:
            print("Creating demo catalog...")
            resp = await client.post(
                f"/api/v1/workspaces/{workspace_id}/catalogs",
                json=DEMO_CATALOG
            )
            resp.raise_for_status()
            catalog_id = resp.json()["catalog"]["id"]
            print(f"Created catalog: {catalog_id}")

        # 3. Load import data
        print(f"Loading data from: {data_file}")
        with open(data_file) as f:
            import_data = json.load(f)

        # 4. Bulk import
        print(f"Importing {len(import_data.get('entities', []))} entities...")
        resp = await client.post(
            f"/api/v1/catalogs/{catalog_id}/import",
            json=import_data,
            timeout=120.0
        )
        resp.raise_for_status()
        result = resp.json()

        print(f"\nImport complete:")
        print(f"  Total: {result['total']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")

        if result.get("job_id"):
            print(f"  Embedding job: {result['job_id']}")

        # Show any failures
        failures = [r for r in result["results"] if not r["success"]]
        if failures:
            print(f"\nFailures:")
            for f in failures[:5]:
                print(f"  - {f['title']}: {f['error']}")
            if len(failures) > 5:
                print(f"  ... and {len(failures) - 5} more")

        return result


async def seed_direct(database_url: str, data_file: Path, user_id: str):
    """Seed data directly into the database."""
    if not HAS_ASYNCPG:
        print("Error: asyncpg not installed. Run: pip install asyncpg")
        sys.exit(1)

    conn = await asyncpg.connect(database_url)

    try:
        # 1. Create or get workspace
        workspace = await conn.fetchrow("""
            INSERT INTO workspaces (name, description, created_by)
            VALUES ($1, $2, $3)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, DEMO_WORKSPACE["name"], DEMO_WORKSPACE["description"], user_id)
        workspace_id = workspace["id"]
        print(f"Workspace ID: {workspace_id}")

        # 2. Add user to workspace
        await conn.execute("""
            INSERT INTO workspace_memberships (workspace_id, user_id, role)
            VALUES ($1, $2, 'owner')
            ON CONFLICT (workspace_id, user_id) DO NOTHING
        """, workspace_id, user_id)

        # 3. Create or get catalog
        catalog = await conn.fetchrow("""
            INSERT INTO catalogs (workspace_id, name, description, content_types, metadata, created_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, workspace_id, DEMO_CATALOG["name"], DEMO_CATALOG["description"],
            DEMO_CATALOG["content_types"], json.dumps(DEMO_CATALOG["metadata"]),
            f"user:{user_id}")

        if catalog:
            catalog_id = catalog["id"]
        else:
            catalog = await conn.fetchrow(
                "SELECT id FROM catalogs WHERE workspace_id = $1 AND name = $2",
                workspace_id, DEMO_CATALOG["name"]
            )
            catalog_id = catalog["id"]
        print(f"Catalog ID: {catalog_id}")

        # 4. Load and insert entities
        with open(data_file) as f:
            import_data = json.load(f)

        entities = import_data.get("entities", [])
        print(f"Inserting {len(entities)} entities...")

        success = 0
        failed = 0

        for entity in entities:
            try:
                await conn.execute("""
                    INSERT INTO rights_entities (
                        catalog_id, rights_type, title, entity_key,
                        content, ai_permissions, ownership_chain, semantic_metadata,
                        status, embedding_status, created_by
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', 'pending', $9)
                    ON CONFLICT (catalog_id, rights_type, entity_key) DO UPDATE
                    SET content = EXCLUDED.content,
                        ai_permissions = EXCLUDED.ai_permissions,
                        ownership_chain = EXCLUDED.ownership_chain,
                        semantic_metadata = EXCLUDED.semantic_metadata,
                        updated_at = now()
                """,
                    catalog_id,
                    entity["rights_type"],
                    entity["title"],
                    entity.get("entity_key"),
                    json.dumps(entity.get("content", {})),
                    json.dumps(entity.get("ai_permissions", {})),
                    json.dumps(entity.get("ownership_chain", [])),
                    json.dumps(entity.get("semantic_metadata", {})),
                    f"user:{user_id}"
                )
                success += 1
            except Exception as e:
                print(f"  Failed: {entity['title']} - {e}")
                failed += 1

        print(f"\nImport complete: {success} success, {failed} failed")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed demo data into Clearinghouse")
    parser.add_argument("--api-url", default=os.getenv("API_URL"), help="API base URL")
    parser.add_argument("--token", default=os.getenv("API_TOKEN"), help="JWT auth token")
    parser.add_argument("--direct", action="store_true", help="Use direct database access")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="Database URL")
    parser.add_argument("--user-id", default=os.getenv("USER_ID"), help="User ID for direct mode")
    parser.add_argument("--data-file", type=Path, help="Path to import data JSON",
                       default=Path(__file__).parent / "test_data" / "kpop_sample.json")

    args = parser.parse_args()

    if not args.data_file.exists():
        print(f"Error: Data file not found: {args.data_file}")
        sys.exit(1)

    import asyncio

    if args.direct:
        if not args.database_url:
            print("Error: --database-url required for direct mode")
            sys.exit(1)
        if not args.user_id:
            print("Error: --user-id required for direct mode")
            sys.exit(1)
        asyncio.run(seed_direct(args.database_url, args.data_file, args.user_id))
    else:
        if not args.api_url or not args.token:
            print("Error: --api-url and --token required for API mode")
            print("       Or use --direct with --database-url for direct DB access")
            sys.exit(1)
        asyncio.run(seed_via_api(args.api_url, args.token, args.data_file))


if __name__ == "__main__":
    main()
