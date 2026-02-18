import json
from datetime import datetime, timezone

from models.database import get_session
from models.db_models import AuditLogEntry


class AuditLogger:
    @classmethod
    def log(cls, action: str, file_id: str = "", user: str = "anonymous", details: dict | None = None):
        session = get_session()
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user=user,
            action=action,
            file_id=file_id,
            details=json.dumps(details or {}),
        )
        session.add(entry)
        session.commit()
        session.close()

    @classmethod
    def get_log(cls, limit: int = 100, file_id: str = "") -> list[dict]:
        session = get_session()
        query = session.query(AuditLogEntry)
        if file_id:
            query = query.filter(AuditLogEntry.file_id == file_id)
        query = query.order_by(AuditLogEntry.id.desc()).limit(limit)
        entries = [e.to_dict() for e in query.all()]
        session.close()
        return list(reversed(entries))
