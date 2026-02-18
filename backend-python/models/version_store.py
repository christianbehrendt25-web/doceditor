import json
import os
import shutil
from datetime import datetime, timezone

import config
from models.database import get_session
from models.db_models import File, FileVersion


class VersionStore:
    @staticmethod
    def _versions_dir(file_id: str) -> str:
        d = os.path.join(config.VERSIONS_DIR, file_id)
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def create_metadata(cls, file_id: str, original_name: str, file_type: str, ext: str) -> dict:
        session = get_session()
        now = datetime.now(timezone.utc)
        f = File(
            file_id=file_id,
            original_name=original_name,
            file_type=file_type,
            ext=ext,
            created_at=now,
            current_version=0,
        )
        v = FileVersion(
            file_id=file_id,
            version=0,
            created_at=now,
            action="upload",
            details="{}",
        )
        session.add(f)
        session.add(v)
        session.commit()
        result = f.to_dict()
        session.close()
        return result

    @classmethod
    def get_metadata(cls, file_id: str) -> dict | None:
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return None
        result = f.to_dict()
        session.close()
        return result

    @classmethod
    def save_metadata(cls, file_id: str, meta: dict):
        """Update file metadata from dict. Kept for compatibility."""
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return
        f.original_name = meta.get("original_name", f.original_name)
        f.current_version = meta.get("current_version", f.current_version)
        session.commit()
        session.close()

    @classmethod
    def get_latest_version_path(cls, file_id: str) -> str | None:
        meta = cls.get_metadata(file_id)
        if not meta:
            return None
        return cls.get_version_path(file_id, meta["current_version"])

    @classmethod
    def get_version_path(cls, file_id: str, version: int) -> str | None:
        meta = cls.get_metadata(file_id)
        if not meta:
            return None
        if version == 0:
            return os.path.join(config.ORIGINALS_DIR, f"{file_id}.{meta['ext']}")
        path = os.path.join(cls._versions_dir(file_id), f"v{version}.{meta['ext']}")
        if os.path.exists(path):
            return path
        return None

    @classmethod
    def create_new_version(cls, file_id: str, source_path: str, action: str, details: dict | None = None) -> int:
        """Copy source_path as a new version. Returns the new version number."""
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            raise ValueError(f"Unknown file: {file_id}")

        new_version = f.current_version + 1
        dest = os.path.join(cls._versions_dir(file_id), f"v{new_version}.{f.ext}")
        shutil.copy2(source_path, dest)

        f.current_version = new_version
        v = FileVersion(
            file_id=file_id,
            version=new_version,
            created_at=datetime.now(timezone.utc),
            action=action,
            details=json.dumps(details or {}),
        )
        session.add(v)
        session.commit()
        session.close()
        return new_version

    @classmethod
    def delete_file(cls, file_id: str):
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return
        ext = f.ext
        session.delete(f)  # cascades to versions
        session.commit()
        session.close()

        # Remove files from filesystem
        orig = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{ext}")
        if os.path.exists(orig):
            os.remove(orig)
        vdir = os.path.join(config.VERSIONS_DIR, file_id)
        if os.path.exists(vdir):
            shutil.rmtree(vdir)

    @classmethod
    def list_files(cls) -> list[dict]:
        session = get_session()
        files = session.query(File).order_by(File.created_at.desc()).all()
        result = [f.to_dict() for f in files]
        session.close()
        return result
