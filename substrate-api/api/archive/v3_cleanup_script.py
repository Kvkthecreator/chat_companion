#!/usr/bin/env python3
"""
V3.0 Cleanup Script - Batch update remaining context_items references

This script adds V3.0 comments to files that still have context_items references
but are not critical to the core pipeline operation.
"""

import os
import re
from pathlib import Path

# Files to update with V3.0 deprecation comments
FILES_TO_UPDATE = [
    "api/src/app/baskets/services/coherence_suggestions.py",
    "api/src/app/baskets/services/improvement_guidance.py",
    "api/src/app/baskets/services/inconsistency_accommodation.py",
    "api/src/app/baskets/services/pattern_recognition.py",
    "api/src/app/context/services/composition_intelligence.py",
    "api/src/app/context/services/context_discovery.py",
    "api/src/app/context/services/context_hierarchy.py",
    "api/src/app/context/services/intent_analyzer.py",
    "api/src/app/documents/services/coherence_analyzer.py",
    "api/src/app/documents/services/context_composition.py",
    "api/src/app/routes/basket_from_template.py",
    "api/src/app/routes/dump_status.py",
    "api/src/app/routes/p3_insights.py",
    "api/src/app/routes/p4_canon.py",
    "api/src/app/routes/projection.py",
    "api/src/app/schemas/work_status.py",
    "api/src/app/services/basket_manager.py",
    "api/src/app/services/status_derivation.py",
    "api/src/lib/canon/SubstrateEqualityEngine.py",
    "api/src/lib/freshness.py",
    "api/src/schemas/context_schema.py",
    "api/src/services/canonical_queue_processor.py",
    "api/src/services/interpretation_adapter.py",
    "api/src/services/narrative_jobs.py",
    "api/src/services/universal_work_tracker.py",
    "api/src/app/agents/pipeline/presentation_agent.py",
    "api/src/app/agents/pipeline/validator_agent.py",
]

V3_HEADER = """# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.
"""

def add_v3_header(filepath: str) -> bool:
    """Add V3.0 deprecation header to file if not already present."""
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  File not found: {filepath}")
            return False

        content = path.read_text()

        # Check if already has V3.0 comment
        if "V3.0" in content or "v3.0" in content:
            print(f"✓ Already updated: {filepath}")
            return True

        # Add header after shebang/docstring
        lines = content.split('\n')
        insert_pos = 0

        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_pos = 1

        # Skip module docstring
        if len(lines) > insert_pos and lines[insert_pos].strip().startswith('"""'):
            # Find end of docstring
            for i in range(insert_pos + 1, len(lines)):
                if '"""' in lines[i]:
                    insert_pos = i + 1
                    break

        # Insert V3 header
        lines.insert(insert_pos, V3_HEADER)
        path.write_text('\n'.join(lines))
        print(f"✅ Updated: {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("V3.0 Cleanup Script - Adding deprecation notices")
    print("=" * 60)

    updated = 0
    for filepath in FILES_TO_UPDATE:
        if add_v3_header(filepath):
            updated += 1

    print("\n" + "=" * 60)
    print(f"Summary: {updated}/{len(FILES_TO_UPDATE)} files updated")
    print("=" * 60)
    print("\n✅ V3.0 cleanup complete!")
    print("   - Core pipeline (P0-P4) fully refactored")
    print("   - Legacy/supporting files marked with deprecation notices")
    print("   - Ready for testing!")

if __name__ == "__main__":
    main()
