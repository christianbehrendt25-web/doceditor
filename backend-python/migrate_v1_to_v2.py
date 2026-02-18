#!/usr/bin/env python3
"""Migration script: DocEditor v1 (FileVersion model) → v2 (current/ + annotations/).

Run once from the backend-python directory:
    python migrate_v1_to_v2.py

What it does:
  1. For each file with current_version > 0, copies the highest version file
     from versions/ to current/<file_id>.<ext>
  2. Drops the file_versions table
  3. Removes the current_version column from the files table
  4. Removes all versions/ subdirectories
"""

import os
import shutil
import sqlite3
import sys

# Ensure backend-python is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def migrate():
    db_path = config.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # --- 1. Copy highest version to current/ ---
    print("Step 1: Migrating version files to current/ …")
    try:
        cur.execute("SELECT file_id, ext, current_version FROM files")
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        # current_version column might already be gone
        print("  current_version column not found, skipping file migration")
        rows = []

    moved = 0
    for row in rows:
        file_id = row["file_id"]
        ext = row["ext"]
        current_v = row["current_version"] if "current_version" in row.keys() else 0

        if current_v == 0:
            continue  # still at original, nothing to migrate

        src = os.path.join(config.VERSIONS_DIR, file_id, f"v{current_v}.{ext}")
        if not os.path.exists(src):
            # Search for the highest available version file
            vdir = os.path.join(config.VERSIONS_DIR, file_id)
            src = None
            if os.path.isdir(vdir):
                candidates = []
                for fn in os.listdir(vdir):
                    if fn.startswith("v") and fn.endswith(f".{ext}"):
                        try:
                            candidates.append(int(fn[1:fn.index(".")]))
                        except ValueError:
                            pass
                if candidates:
                    best = max(candidates)
                    src = os.path.join(vdir, f"v{best}.{ext}")

        if src and os.path.exists(src):
            dest = os.path.join(config.CURRENT_DIR, f"{file_id}.{ext}")
            shutil.copy2(src, dest)
            print(f"  {file_id}: v{current_v} → current/")
            moved += 1
        else:
            print(f"  {file_id}: no version file found, skipping")

    print(f"  Migrated {moved} file(s) to current/\n")

    # --- 2. Drop file_versions table ---
    print("Step 2: Dropping file_versions table …")
    try:
        cur.execute("DROP TABLE IF EXISTS file_versions")
        conn.commit()
        print("  Done\n")
    except Exception as e:
        print(f"  Warning: {e}\n")

    # --- 3. Remove current_version column ---
    print("Step 3: Removing current_version column from files …")
    try:
        cur.execute("ALTER TABLE files DROP COLUMN current_version")
        conn.commit()
        print("  Dropped column directly\n")
    except sqlite3.OperationalError as e:
        print(f"  Direct DROP COLUMN failed ({e}), recreating table …")
        # Fallback: recreate table without current_version
        cur.execute("""
            CREATE TABLE IF NOT EXISTS files_v2 (
                file_id   TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                ext       TEXT NOT NULL,
                created_at DATETIME
            )
        """)
        cur.execute("""
            INSERT OR IGNORE INTO files_v2 (file_id, original_name, file_type, ext, created_at)
            SELECT file_id, original_name, file_type, ext, created_at FROM files
        """)
        cur.execute("DROP TABLE files")
        cur.execute("ALTER TABLE files_v2 RENAME TO files")
        conn.commit()
        print("  Recreated files table without current_version\n")

    # --- 4. Remove versions/ subdirectories ---
    print("Step 4: Cleaning up versions/ subdirectories …")
    removed = 0
    if os.path.isdir(config.VERSIONS_DIR):
        for name in os.listdir(config.VERSIONS_DIR):
            full = os.path.join(config.VERSIONS_DIR, name)
            if os.path.isdir(full):
                shutil.rmtree(full)
                print(f"  Removed versions/{name}")
                removed += 1
    print(f"  Removed {removed} director(y/ies)\n")

    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    print("DocEditor v1 → v2 Migration")
    print("=" * 40)
    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)
    print()
    migrate()
