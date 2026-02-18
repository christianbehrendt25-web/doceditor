#!/usr/bin/env python3
"""One-time migration: import existing JSON metadata into SQLAlchemy DB."""
import json
import os
import sys
from datetime import datetime

import config
from models.database import init_db, get_session
from models.db_models import File, FileVersion

init_db(config.DATABASE_URL)
session = get_session()

count = 0
for fname in os.listdir(config.METADATA_DIR):
    if not fname.endswith(".json"):
        continue
    file_id = fname[:-5]

    # Skip if already in DB
    if session.get(File, file_id):
        print(f"  SKIP {file_id} (already in DB)")
        continue

    with open(os.path.join(config.METADATA_DIR, fname)) as f:
        meta = json.load(f)

    file_obj = File(
        file_id=meta["file_id"],
        original_name=meta["original_name"],
        file_type=meta["file_type"],
        ext=meta["ext"],
        created_at=datetime.fromisoformat(meta["created_at"]),
        current_version=meta["current_version"],
    )
    session.add(file_obj)

    for v in meta.get("versions", []):
        version_obj = FileVersion(
            file_id=meta["file_id"],
            version=v["version"],
            created_at=datetime.fromisoformat(v["created_at"]),
            action=v["action"],
            details=json.dumps(v.get("details", {})),
        )
        session.add(version_obj)

    count += 1
    print(f"  Migrated: {file_id} ({meta['original_name']})")

session.commit()
session.close()
print(f"\nDone. Migrated {count} file(s).")
