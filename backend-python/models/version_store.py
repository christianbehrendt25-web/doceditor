import json
import os
import shutil
from datetime import datetime, timezone

import config


class VersionStore:
    @staticmethod
    def _meta_path(file_id: str) -> str:
        return os.path.join(config.METADATA_DIR, f"{file_id}.json")

    @staticmethod
    def _versions_dir(file_id: str) -> str:
        d = os.path.join(config.VERSIONS_DIR, file_id)
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def create_metadata(cls, file_id: str, original_name: str, file_type: str, ext: str) -> dict:
        meta = {
            "file_id": file_id,
            "original_name": original_name,
            "file_type": file_type,
            "ext": ext,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_version": 0,
            "versions": [
                {
                    "version": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "action": "upload",
                    "details": {},
                }
            ],
        }
        with open(cls._meta_path(file_id), "w") as f:
            json.dump(meta, f, indent=2)
        return meta

    @classmethod
    def get_metadata(cls, file_id: str) -> dict | None:
        path = cls._meta_path(file_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def save_metadata(cls, file_id: str, meta: dict):
        with open(cls._meta_path(file_id), "w") as f:
            json.dump(meta, f, indent=2)

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
        meta = cls.get_metadata(file_id)
        if not meta:
            raise ValueError(f"Unknown file: {file_id}")
        new_version = meta["current_version"] + 1
        dest = os.path.join(cls._versions_dir(file_id), f"v{new_version}.{meta['ext']}")
        shutil.copy2(source_path, dest)
        meta["current_version"] = new_version
        meta["versions"].append({
            "version": new_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details or {},
        })
        cls.save_metadata(file_id, meta)
        return new_version

    @classmethod
    def delete_file(cls, file_id: str):
        meta = cls.get_metadata(file_id)
        if not meta:
            return
        # Remove original
        orig = os.path.join(config.ORIGINALS_DIR, f"{file_id}.{meta['ext']}")
        if os.path.exists(orig):
            os.remove(orig)
        # Remove versions dir
        vdir = os.path.join(config.VERSIONS_DIR, file_id)
        if os.path.exists(vdir):
            shutil.rmtree(vdir)
        # Remove metadata
        mp = cls._meta_path(file_id)
        if os.path.exists(mp):
            os.remove(mp)

    @classmethod
    def list_files(cls) -> list[dict]:
        files = []
        for fname in os.listdir(config.METADATA_DIR):
            if not fname.endswith(".json"):
                continue
            file_id = fname[:-5]
            meta = cls.get_metadata(file_id)
            if meta:
                files.append(meta)
        files.sort(key=lambda m: m["created_at"], reverse=True)
        return files
