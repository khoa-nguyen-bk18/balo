#!/usr/bin/env python3
"""
cas_integrity_scrub.py
======================
Audits and verifies the SHA-256 cryptographic integrity of all physical CAS blobs
against their recorded hashes in the SQLite database.
"""

import os
import sys
import hashlib
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CASScrub")

def verify_cas_repository(db_path: str, repo_root: str) -> bool:
    if not os.path.isfile(db_path):
        logger.error("Database file not found: %s", db_path)
        return False

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT sha256_hash, size_bytes, storage_relpath FROM file_blobs")
    rows = cursor.fetchall()

    corruptions = 0
    missing = 0
    verified = 0

    logger.info("Beginning cryptographic CAS integrity scrub of %d registered blobs...", len(rows))

    for idx, row in enumerate(rows, 1):
        expected_hash = row["sha256_hash"]
        full_path = os.path.join(repo_root, row["storage_relpath"])

        if not os.path.exists(full_path):
            logger.error("[MISSING] Blob not found on disk: %s", full_path)
            missing += 1
            continue

        hasher = hashlib.sha256()
        try:
            with open(full_path, "rb") as f:
                while chunk := f.read(1048576):
                    hasher.update(chunk)
            actual_hash = hasher.hexdigest()

            if actual_hash != expected_hash:
                logger.error("[CORRUPTED] Hash mismatch for %s (Expected: %s, Got: %s)", full_path, expected_hash, actual_hash)
                corruptions += 1
            else:
                verified += 1
        except Exception as e:
            logger.error("[ERROR] Failed reading blob %s: %s", full_path, e)
            corruptions += 1

        if idx % 1000 == 0:
            logger.info("Scrubbed %d / %d blobs...", idx, len(rows))

    logger.info("Integrity Scrub Completed: Verified=%d | Corrupted=%d | Missing=%d", verified, corruptions, missing)
    return (corruptions == 0 and missing == 0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 cas_integrity_scrub.py <path_to_zalo_backup.db> <workspace_root>")
        sys.exit(1)
    
    db_arg = sys.argv[1]
    repo_arg = sys.argv[2]
    success = verify_cas_repository(db_arg, repo_arg)
    sys.exit(0 if success else 1)
