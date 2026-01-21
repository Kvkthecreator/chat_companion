from datetime import datetime
from uuid import uuid4

from infra.substrate.models.raw_dump import RawDump


def test_raw_dump_accepts_document_id():
    rd = RawDump(
        id=uuid4(),
        basket_id=uuid4(),
        document_id=uuid4(),
        created_at=datetime.utcnow(),
        workspace_id=uuid4(),
    )
    assert rd.document_id is not None
