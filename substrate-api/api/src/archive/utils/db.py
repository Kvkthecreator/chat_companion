from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

JSONable = str | int | float | bool | None | Mapping | list


def json_safe(record: Mapping[str, Any]) -> dict[str, JSONable]:
    """Return copy with datetimes, dates, and Decimals converted."""
    out: dict[str, JSONable] = {}
    for k, v in record.items():
        if v is None:
            continue
        if isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out
