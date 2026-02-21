"""Purge archived snapshots older than the retention window.

This script:
- Deletes rows in `archived_entities` older than 30 days (or the row's
  `purge_after_days`).
- For soft-archived entities that still exist (users/admins), it will
  permanently delete them once their archive record expires.

Run via scheduler (cron/Task Scheduler) daily.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app  # noqa: E402
from database import db, ArchivedEntity, Admin, Assessment, User  # noqa: E402


def purge_archives(default_retention_days: int = 30) -> dict:
    deleted_archive_rows = 0
    deleted_users = 0
    deleted_admins = 0
    deleted_assessments = 0

    now = datetime.utcnow()

    # Load candidates in manageable batches.
    candidates = ArchivedEntity.query.order_by(ArchivedEntity.archived_at.asc()).all()

    for row in candidates:
        retention_days = row.purge_after_days or default_retention_days
        cutoff = now - timedelta(days=int(retention_days))
        if not row.archived_at or row.archived_at >= cutoff:
            continue

        # Purge soft-archived underlying entities once the archive expires.
        if row.entity_type == 'user':
            user = User.query.get(row.entity_id)
            if user and (user.status == 'archived'):
                deleted_assessments += (
                    Assessment.query.filter_by(user_id=user.user_id).delete(synchronize_session=False)
                )
                db.session.delete(user)
                deleted_users += 1

        elif row.entity_type == 'admin':
            try:
                admin_id = int(row.entity_id)
            except Exception:
                admin_id = None

            if admin_id is not None:
                admin = Admin.query.get(admin_id)
                # Archived admins are represented by the archive row plus an
                # inactive status (legacy schemas may not accept 'archived').
                if admin and (admin.status in ('inactive', '', None)):
                    db.session.delete(admin)
                    deleted_admins += 1

        db.session.delete(row)
        deleted_archive_rows += 1

    db.session.commit()

    return {
        'deleted_archive_rows': deleted_archive_rows,
        'deleted_users': deleted_users,
        'deleted_admins': deleted_admins,
        'deleted_assessments': deleted_assessments,
    }


if __name__ == '__main__':
    with app.app_context():
        result = purge_archives()
        print('Archive purge complete:', result)
