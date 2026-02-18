from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from models.database import Base


class File(Base):
    __tablename__ = "files"

    file_id = Column(String(64), primary_key=True)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # "pdf" or "image"
    ext = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    current_version = Column(Integer, default=0)

    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan",
                            order_by="FileVersion.version")

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "ext": self.ext,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
        }


class FileVersion(Base):
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(64), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    action = Column(String(64), nullable=False)
    details = Column(Text, default="{}")  # JSON string

    file = relationship("File", back_populates="versions")

    def to_dict(self) -> dict:
        import json
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "action": self.action,
            "details": json.loads(self.details) if self.details else {},
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
