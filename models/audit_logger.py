import json
import threading
from datetime import datetime, timezone

import config


class AuditLogger:
    _lock = threading.Lock()

    @classmethod
    def log(cls, action: str, file_id: str = "", user: str = "anonymous", details: dict | None = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": action,
            "file_id": file_id,
            "details": details or {},
        }
        with cls._lock:
            with open(config.AUDIT_LOG_PATH, "a") as f:
                f.write(json.dumps(entry) + "\n")

    @classmethod
    def get_log(cls, limit: int = 100, file_id: str = "") -> list[dict]:
        entries = []
        try:
            with open(config.AUDIT_LOG_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    if file_id and entry.get("file_id") != file_id:
                        continue
                    entries.append(entry)
        except FileNotFoundError:
            pass
        return entries[-limit:]
