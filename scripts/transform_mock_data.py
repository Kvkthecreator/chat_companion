#!/usr/bin/env python3
"""
Transform mock data from demo format to Clearinghouse bulk import format.

Input: tracks_all.json (rich track data with nested structures)
Output: import_ready.json (flat structure matching bulk import API)

Usage:
    python transform_mock_data.py /path/to/tracks_all.json
"""

import json
import sys
from pathlib import Path


def transform_track(track: dict) -> dict:
    """Transform a single track to bulk import format."""

    # Extract content (type-specific metadata that goes in 'content' JSONB)
    content = {
        "title_kr": track.get("title_kr"),
        "artist_id": track.get("artist_id"),
        "artist_name": track.get("artist_name"),
        "album": track.get("album"),
        "album_type": track.get("album_type"),
        "upc": track.get("upc"),
        "duration_seconds": track.get("duration_seconds"),
        "release_date": track.get("release_date"),
        "genre": track.get("genre", []),
        "subgenre": track.get("subgenre", []),
        "language": track.get("language"),
        "explicit": track.get("explicit", False),
        "audio_features": track.get("audio_features", {}),
        "label_id": track.get("label_id"),
    }

    # Semantic metadata (for embedding generation)
    semantic_metadata = {
        "mood_tags": track.get("mood_tags", []),
        "theme_tags": track.get("theme_tags", []),
        "instrument_tags": track.get("instrument_tags", []),
        "vocal_tags": track.get("vocal_tags", []),
    }

    # Remove None values from content
    content = {k: v for k, v in content.items() if v is not None}

    # AI permissions - already in correct format, just pass through
    ai_permissions = track.get("ai_permissions", {})

    # Ownership chain from rights structure
    rights = track.get("rights", {})
    ownership_chain = []

    # Add composition rights
    composition = rights.get("composition", {})
    for writer in composition.get("writers", []):
        ownership_chain.append({
            "type": "composition",
            "role": "writer",
            "name": writer.get("name"),
            "name_kr": writer.get("name_kr"),
            "ipi": writer.get("ipi"),
            "share": writer.get("share")
        })
    for publisher in composition.get("publishers", []):
        ownership_chain.append({
            "type": "composition",
            "role": "publisher",
            "name": publisher.get("name"),
            "share": publisher.get("share")
        })

    # Add master rights
    master = rights.get("master", {})
    if master:
        ownership_chain.append({
            "type": "master",
            "role": "owner",
            "name": master.get("owner"),
            "share": master.get("share"),
            "territory": rights.get("territory", "worldwide")
        })

    # Handle co-ownership if present
    if "co_owner" in master:
        ownership_chain.append({
            "type": "master",
            "role": "co_owner",
            "name": master.get("co_owner"),
            "share": master.get("co_owner_share")
        })

    # Build the import-ready entity
    return {
        "rights_type": "sound_recording",
        "title": track["title"],
        "entity_key": track.get("isrc"),  # ISRC as external identifier
        "content": content,
        "ai_permissions": ai_permissions,
        "ownership_chain": ownership_chain,
        "semantic_metadata": semantic_metadata,
    }


def transform_file(input_path: Path) -> dict:
    """Transform entire tracks file."""
    with open(input_path) as f:
        data = json.load(f)

    tracks = data.get("tracks", data) if isinstance(data, dict) else data

    transformed = []
    for track in tracks:
        try:
            transformed.append(transform_track(track))
        except Exception as e:
            print(f"Warning: Failed to transform track {track.get('id', 'unknown')}: {e}")

    return {
        "entities": transformed,
        "auto_process": True,  # Queue embedding generation
        "metadata": {
            "source": str(input_path),
            "total_tracks": len(transformed),
            "rights_type": "sound_recording"
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python transform_mock_data.py <input_file.json> [output_file.json]")
        print("\nTransforms demo track data to Clearinghouse bulk import format.")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.parent / "import_ready.json"

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Transforming: {input_path}")
    result = transform_file(input_path)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Output written to: {output_path}")
    print(f"Total entities: {result['metadata']['total_tracks']}")
    print(f"\nReady for bulk import via POST /api/v1/catalogs/{{catalog_id}}/import")


if __name__ == "__main__":
    main()
