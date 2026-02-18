from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from models.database import Base


class File(Base):
    __tablename__ = "files"

    file_id = Column(String(64), primary_key=True)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # "pdf" or "image"
    ext = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "ext": self.ext,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = Column(String(128), default="anonymous")
    action = Column(String(64), nullable=False)
    file_id = Column(String(64), default="")
    details = Column(Text, default="{}")  # JSON string

    def to_dict(self) -> dict:
        import json
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user": self.user,
            "action": self.action,
            "file_id": self.file_id,
            "details": json.loads(self.details) if self.details else {},
        }
