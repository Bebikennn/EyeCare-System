"""Archive helpers for delete operations."""

from __future__ import annotations

import json
from typing import Any, Optional

from database import ArchivedEntity, db


def archive_entity(
    *,
    entity_type: str,
    entity_id: str,
    data: Any,
    archived_by_admin_id: Optional[int] = None,
    purge_after_days: int = 30,
    reason: Optional[str] = None,
) -> ArchivedEntity:
    """Create an ArchivedEntity row for the given entity.

    This does not commit; caller should commit with its other DB changes.
    """

    payload = json.dumps(data, default=str)
    archive_row = ArchivedEntity(
        entity_type=entity_type,
        entity_id=str(entity_id),
        data_json=payload,
        archived_by_admin_id=archived_by_admin_id,
        purge_after_days=purge_after_days,
        reason=reason,
    )
    db.session.add(archive_row)
    return archive_row
