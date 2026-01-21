from app.util.snapshot_assembler import assemble_snapshot


def test_assemble_filters_states():
    blocks = [
        {"id": "1", "state": "ACCEPTED"},
        {"id": "2", "state": "PROPOSED"},
        {"id": "3", "state": "LOCKED"},
        {"id": "4", "state": "CONSTANT"},
    ]
    raw = [{"body_md": "a", "created_at": "t"}]
    snap = assemble_snapshot(raw, blocks)
    assert len(snap["accepted_blocks"]) == 1
    assert len(snap["locked_blocks"]) == 1
    assert len(snap["proposed_blocks"]) == 1
    assert len(snap["constants"]) == 1
    assert snap["raw_dump"] == "a"
