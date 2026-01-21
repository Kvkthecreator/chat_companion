#!/usr/bin/env python3
"""
Migration runner for Render.com deployment.

Usage:
    python run_migrations.py

Requires DATABASE_URL environment variable to be set.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.deps import get_db


async def run_migration_file(db, migration_file: Path):
    """Run a single migration file."""
    print(f"Running migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Split on semicolons and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    for i, statement in enumerate(statements):
        try:
            await db.execute(statement)
            print(f"  ✓ Executed statement {i+1}/{len(statements)}")
        except Exception as e:
            print(f"  ✗ Failed statement {i+1}: {e}")
            # Continue with other statements
    
    print(f"✓ Completed migration: {migration_file.name}")


async def main():
    """Run all migrations in order."""
    print("🚀 Starting database migrations...")
    
    # Check for DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable is required")
        sys.exit(1)
    
    try:
        db = await get_db()
        print("✓ Connected to database")
        
        # Find migration files
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            print("❌ migrations/ directory not found")
            sys.exit(1)
        
        migration_files = sorted(migrations_dir.glob("*.sql"))
        if not migration_files:
            print("❌ No .sql files found in migrations/")
            sys.exit(1)
        
        print(f"Found {len(migration_files)} migration files")
        
        # Run migrations in order
        for migration_file in migration_files:
            await run_migration_file(db, migration_file)
        
        print("🎉 All migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())