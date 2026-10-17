#!/usr/bin/env python3
"""
restore_zalo_export.py
======================
Reconstitutes and exports files from the Content-Addressable Storage (CAS)
repository back into their original names and folder hierarchy.
"""

import os
import sys
import shutil
import sqlite3
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RestoreZalo")

def restore_files(db_path: str, repo_root: str, dest_dir: str, category: str = None, mode: str = "hardlink"):
    if not os.path.isfile(db_path):
        logger.error("Database not found: %s", db_path)
        sys.exit(1)

    os.makedirs(dest_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT r.original_path, r.filename, r.category, b.storage_relpath
        FROM file_records r
        JOIN file_blobs b ON r.blob_hash = b.sha256_hash
    """
    params = []
    if category:
        query += " WHERE r.category = ?"
        params.append(category)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    logger.info("Reconstituting %d files into '%s' (mode: %s)...", len(rows), dest_dir, mode)
    restored = 0

    for row in rows:
        src_blob = os.path.join(repo_root, row["storage_relpath"])
        if not os.path.isfile(src_blob):
            continue

        # Recreate subfolder based on original path relative to Zalo root
        clean_rel = row["original_path"].lstrip("/")
        marker = "com.zing.zalo/files/zalo/"
        if marker in clean_rel:
            rel_path = clean_rel.split(marker, 1)[1]
        else:
            rel_path = os.path.join(row["category"], row["filename"])

        target_path = os.path.join(dest_dir, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        try:
            if os.path.exists(target_path):
                os.remove(target_path)
            if mode == "hardlink":
                os.link(src_blob, target_path)
            elif mode == "symlink":
                os.symlink(os.path.relpath(src_blob, os.path.dirname(target_path)), target_path)
            else:
                shutil.copy2(src_blob, target_path)
            restored += 1
        except Exception as e:
            logger.warning("Failed to restore %s: %s", target_path, e)

    logger.info("Successfully reconstituted %d / %d files to %s.", restored, len(rows), os.path.abspath(dest_dir))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstitute Zalo files from CAS repository")
    parser.add_argument("--db", default="./zalo_backup.db", help="Path to zalo_backup.db")
    parser.add_argument("--workspace", default=".", help="Workspace containing objects/ directory")
    parser.add_argument("--dest", default="./reconstituted_zalo", help="Output directory")
    parser.add_argument("--category", default=None, help="Filter by category (picture, video, downloads, file_resource, etc.)")
    parser.add_argument("--mode", choices=["hardlink", "copy", "symlink"], default="hardlink", help="Restore method (default: hardlink)")
    args = parser.parse_args()

    restore_files(args.db, args.workspace, args.dest, args.category, args.mode)
