import json
import os
import shutil
from datetime import datetime, timezone

import config


class AnnotationStore:
    @staticmethod
    def _path(file_id: str, user: str) -> str:
        d = os.path.join(config.ANNOTATIONS_DIR, file_id)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{user}.json")

    @staticmethod
    def list_users(file_id: str) -> list[str]:
        d = os.path.join(config.ANNOTATIONS_DIR, file_id)
        if not os.path.isdir(d):
            return []
        return [fn[:-5] for fn in os.listdir(d) if fn.endswith(".json")]

    @classmethod
    def get(cls, file_id: str, user: str) -> dict:
        path = cls._path(file_id, user)
        if not os.path.exists(path):
            return {"user": user, "updated_at": None, "fabric_pages": {}, "text_overlays": []}
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @classmethod
    def save(cls, file_id: str, user: str, data: dict):
        data["user"] = user
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        path = cls._path(file_id, user)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    @classmethod
    def delete(cls, file_id: str, user: str):
        path = cls._path(file_id, user)
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def delete_all(file_id: str):
        d = os.path.join(config.ANNOTATIONS_DIR, file_id)
        if os.path.isdir(d):
            shutil.rmtree(d)
