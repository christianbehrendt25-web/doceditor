import os
import shutil
from datetime import datetime, timezone

import config
from models.database import get_session
from models.db_models import File


class VersionStore:
    @staticmethod
    def get_original_path(file_id: str) -> str | None:
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return None
        path = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{f.ext}")
        session.close()
        return path

    @staticmethod
    def get_current_path(file_id: str) -> str | None:
        """Return current/ path if it exists, otherwise fall back to original."""
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return None
        ext = f.ext
        session.close()
        current = os.path.join(config.CURRENT_DIR, f"{file_id}.{ext}")
        if os.path.exists(current):
            return current
        original = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{ext}")
        return original if os.path.exists(original) else None

    @classmethod
    def update_current(cls, file_id: str, source_path: str):
        """Replace the current/ file with a copy of source_path."""
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            raise ValueError(f"Unknown file: {file_id}")
        ext = f.ext
        session.close()
        dest = os.path.join(config.CURRENT_DIR, f"{file_id}.{ext}")
        if os.path.exists(dest):
            os.remove(dest)
        shutil.copy2(source_path, dest)

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
        )
        session.add(f)
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
    def delete_file(cls, file_id: str):
        from models.annotation_store import AnnotationStore
        session = get_session()
        f = session.get(File, file_id)
        if not f:
            session.close()
            return
        ext = f.ext
        session.delete(f)
        session.commit()
        session.close()

        orig = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{ext}")
        if os.path.exists(orig):
            os.remove(orig)
        curr = os.path.join(config.CURRENT_DIR, f"{file_id}.{ext}")
        if os.path.exists(curr):
            os.remove(curr)
        AnnotationStore.delete_all(file_id)

    @classmethod
    def list_files(cls) -> list[dict]:
        session = get_session()
        files = session.query(File).order_by(File.created_at.desc()).all()
        result = [f.to_dict() for f in files]
        session.close()
        return result
