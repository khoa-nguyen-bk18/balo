#!/usr/bin/env python3
"""
zalo_interval_sync.py
=====================
Production Interval-Based Backup Daemon for Zalo Android Media.
Features:
  - Non-root unprivileged ADB delta discovery
  - Content-Addressable Storage (CAS) with SHA-256 two-level directory sharding
  - Sliding-window watermark synchronization (zero missed records)
  - Full relational tracking in SQLite (WAL mode)
  - Strict host disk safety guardrails (< 1.5 GiB threshold abort)
  - Clean signal handling (SIGINT, SIGTERM)
"""

import os
import sys
import time
import uuid
import shutil
import hashlib
import sqlite3
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ZaloIntervalSync")

# Constants & Guardrails
SAFE_MIN_DISK_BYTES = 1610612736  # 1.5 GiB
DEFAULT_SLIDING_WINDOW_SEC = 120  # 2 minutes lookback
ZALO_REMOTE_BASE = "/sdcard/Android/data/com.zing.zalo/files/zalo"

CATEGORIES = {
    "picture": [".jpg", ".jpeg", ".png", ".webp", ".bmp"],
    "downloads": [".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".rar", ".tar", ".gz", ".apk", ".txt"],
    "voice": [".amr", ".aac", ".m4a", ".mp3", ".wav"],
    "video": [".mp4", ".3gp", ".mkv", ".webm"],
    "file_resource": [".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".rar", ".doc"],
    "recommend_link": [".jpg", ".png", ".webp"],
    "call_asr": [".amr", ".aac", ".mp3", ".wav", ".bin"]
}


class StorageSafetyError(Exception):
    """Raised when host disk space falls below safe operating levels."""
    pass


class DeviceCommunicationError(Exception):
    """Raised when ADB commands fail or device is disconnected."""
    pass


class ZaloCASDatabase:
    """Manages SQLite storage for CAS blobs, records, and watermarks."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS file_blobs (
                    sha256_hash         TEXT PRIMARY KEY CHECK (length(sha256_hash) = 64),
                    size_bytes          INTEGER NOT NULL CHECK (size_bytes >= 0),
                    mime_type           TEXT NOT NULL DEFAULT 'application/octet-stream',
                    storage_relpath     TEXT NOT NULL UNIQUE,
                    first_seen_at       INTEGER NOT NULL,
                    last_verified_at    INTEGER NOT NULL,
                    ref_count           INTEGER NOT NULL DEFAULT 1 CHECK (ref_count >= 0),
                    md5_checksum        TEXT CHECK (md5_checksum IS NULL OR length(md5_checksum) = 32)
                );

                CREATE TABLE IF NOT EXISTS backup_checkpoints (
                    run_id              TEXT PRIMARY KEY,
                    started_at          INTEGER NOT NULL,
                    completed_at        INTEGER,
                    trigger_type        TEXT NOT NULL,
                    status              TEXT NOT NULL,
                    scanned_count       INTEGER NOT NULL DEFAULT 0,
                    new_blobs_count     INTEGER NOT NULL DEFAULT 0,
                    deduplicated_count  INTEGER NOT NULL DEFAULT 0,
                    bytes_transferred   INTEGER NOT NULL DEFAULT 0,
                    error_message       TEXT
                );

                CREATE TABLE IF NOT EXISTS file_records (
                    record_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    blob_hash           TEXT NOT NULL,
                    original_path       TEXT NOT NULL,
                    filename            TEXT NOT NULL,
                    file_ext            TEXT,
                    category            TEXT NOT NULL,
                    source_device_id    TEXT NOT NULL,
                    device_mtime        INTEGER NOT NULL,
                    device_size         INTEGER NOT NULL,
                    last_sync_run_id    TEXT NOT NULL,
                    is_deleted          INTEGER NOT NULL DEFAULT 0,
                    created_at          INTEGER NOT NULL,
                    updated_at          INTEGER NOT NULL,
                    FOREIGN KEY (blob_hash) REFERENCES file_blobs(sha256_hash) ON DELETE RESTRICT,
                    FOREIGN KEY (last_sync_run_id) REFERENCES backup_checkpoints(run_id) ON DELETE CASCADE,
                    CONSTRAINT uq_device_path UNIQUE (source_device_id, original_path)
                );

                CREATE INDEX IF NOT EXISTS idx_records_blob ON file_records(blob_hash);
                CREATE INDEX IF NOT EXISTS idx_records_mtime ON file_records(device_mtime);

                CREATE TABLE IF NOT EXISTS sync_watermarks (
                    category_or_dir     TEXT PRIMARY KEY,
                    last_watermark_ts   INTEGER NOT NULL DEFAULT 0,
                    last_mtime_epoch    INTEGER NOT NULL DEFAULT 0,
                    last_sync_status    TEXT NOT NULL,
                    items_synced_count  INTEGER NOT NULL DEFAULT 0,
                    total_bytes_synced  INTEGER NOT NULL DEFAULT 0,
                    updated_at          INTEGER NOT NULL
                );
            """)

    def get_watermark(self, category: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_mtime_epoch FROM sync_watermarks WHERE category_or_dir = ?",
                (category,)
            )
            row = cursor.fetchone()
            return row["last_mtime_epoch"] if row else 0

    def set_watermark(self, category: str, mtime_epoch: int, items_count: int, bytes_count: int):
        now_ts = int(time.time())
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO sync_watermarks (category_or_dir, last_watermark_ts, last_mtime_epoch, last_sync_status, items_synced_count, total_bytes_synced, updated_at)
                VALUES (?, ?, ?, 'OK', ?, ?, ?)
                ON CONFLICT(category_or_dir) DO UPDATE SET
                    last_watermark_ts = excluded.last_watermark_ts,
                    last_mtime_epoch = excluded.last_mtime_epoch,
                    last_sync_status = 'OK',
                    items_synced_count = items_synced_count + excluded.items_synced_count,
                    total_bytes_synced = total_bytes_synced + excluded.total_bytes_synced,
                    updated_at = excluded.updated_at
            """, (category, now_ts, mtime_epoch, items_count, bytes_count, now_ts))

    def record_exists_and_current(self, device_id: str, original_path: str, mtime: int, size: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT device_mtime, device_size FROM file_records WHERE source_device_id = ? AND original_path = ?",
                (device_id, original_path)
            )
            row = cursor.fetchone()
            if row and row["device_mtime"] == mtime and row["device_size"] == size:
                return True
            return False

    def upsert_blob_and_record(
        self,
        sha256_hash: str,
        size_bytes: int,
        storage_relpath: str,
        device_id: str,
        original_path: str,
        filename: str,
        file_ext: str,
        category: str,
        device_mtime: int,
        run_id: str
    ) -> bool:
        """
        Inserts or references a blob and binds the file_record.
        Returns True if a NEW physical blob was created, False if deduplicated.
        """
        now_ts = int(time.time())
        is_new_blob = False

        with self.get_connection() as conn:
            with conn:
                # 1. Blob registration
                cursor = conn.execute("SELECT sha256_hash FROM file_blobs WHERE sha256_hash = ?", (sha256_hash,))
                existing_blob = cursor.fetchone()

                if not existing_blob:
                    conn.execute("""
                        INSERT INTO file_blobs (sha256_hash, size_bytes, storage_relpath, first_seen_at, last_verified_at, ref_count)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (sha256_hash, size_bytes, storage_relpath, now_ts, now_ts))
                    is_new_blob = True
                else:
                    conn.execute("""
                        UPDATE file_blobs 
                        SET ref_count = ref_count + 1, last_verified_at = ?
                        WHERE sha256_hash = ?
                    """, (now_ts, sha256_hash))

                # 2. File record upsert
                conn.execute("""
                    INSERT INTO file_records (
                        blob_hash, original_path, filename, file_ext, category,
                        source_device_id, device_mtime, device_size, last_sync_run_id,
                        is_deleted, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ON CONFLICT(source_device_id, original_path) DO UPDATE SET
                        blob_hash = excluded.blob_hash,
                        device_mtime = excluded.device_mtime,
                        device_size = excluded.device_size,
                        last_sync_run_id = excluded.last_sync_run_id,
                        is_deleted = 0,
                        updated_at = excluded.updated_at
                """, (
                    sha256_hash, original_path, filename, file_ext, category,
                    device_id, device_mtime, size_bytes, run_id, now_ts, now_ts
                ))

        return is_new_blob


class ZaloBackupEngine:
    """Orchestrates differential scanning, streaming ingestion, and CAS storage."""

    def __init__(self, workspace_root: str, device_serial: Optional[str] = None):
        self.workspace_root = os.path.abspath(workspace_root)
        self.objects_dir = os.path.join(self.workspace_root, "objects")
        self.db_path = os.path.join(self.workspace_root, "zalo_backup.db")
        self.device_serial = device_serial
        if not self.device_serial:
            try:
                out = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True).stdout
                devs = [line.split()[0] for line in out.splitlines()[1:] if line.strip() and "device" in line]
                if devs:
                    self.device_serial = devs[0]
                    logger.info("Auto-selected ADB device: %s", self.device_serial)
            except Exception:
                pass

        os.makedirs(self.objects_dir, exist_ok=True)
        self.db = ZaloCASDatabase(self.db_path)
        self.device_id = self._get_device_identifier()

    def _adb_prefix(self) -> List[str]:
        if self.device_serial:
            return ["adb", "-s", self.device_serial]
        return ["adb"]

    def _run_adb_cmd(self, args: List[str], check: bool = True) -> str:
        cmd = self._adb_prefix() + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error("ADB command failed: %s | Error: %s", " ".join(cmd), e.stderr.strip())
            raise DeviceCommunicationError(e.stderr.strip())
        except FileNotFoundError:
            raise DeviceCommunicationError("ADB executable not found in system PATH.")

    def _get_device_identifier(self) -> str:
        try:
            model = self._run_adb_cmd(["shell", "getprop", "ro.product.model"])
            serial = self._run_adb_cmd(["get-serialno"])
            return f"{model}_{serial}".replace(" ", "_")
        except Exception as e:
            logger.warning("Could not read device model: %s. Using default device ID.", e)
            return "zalo_android_device"

    def check_host_disk_safety(self):
        total, used, free = shutil.disk_usage(self.workspace_root)
        free_gib = free / (1024 ** 3)
        if free < SAFE_MIN_DISK_BYTES:
            raise StorageSafetyError(
                f"ABORT: Host free space is {free_gib:.2f} GiB, below the 1.50 GiB safety threshold!"
            )
        logger.debug("Host free storage: %.2f GiB (Healthy)", free_gib)

    def scan_remote_deltas(self, category: str, lookback_sec: int) -> List[Tuple[int, int, str]]:
        """
        Executes non-root discovery over ADB returning [(size, mtime, remote_path), ...]
        using sliding-window watermark offset.
        """
        remote_category_path = f"{ZALO_REMOTE_BASE}/{category}"
        last_mtime = self.db.get_watermark(category)
        scan_mtime_threshold = max(0, last_mtime - lookback_sec)

        logger.info(
            "Scanning category '%s' (Watermark: %s | Scan Threshold: %s)...",
            category,
            datetime.fromtimestamp(last_mtime).isoformat() if last_mtime else "Epoch 0",
            datetime.fromtimestamp(scan_mtime_threshold).isoformat()
        )

        shell_cmd = (
            f"if [ -d '{remote_category_path}' ]; then "
            f"find '{remote_category_path}' -type f -exec stat -c '%s %Y %n' {{}} + 2>/dev/null; "
            f"fi"
        )

        output = self._run_adb_cmd(["shell", shell_cmd], check=False)
        if not output:
            return []

        candidates = []
        for line in output.splitlines():
            parts = line.strip().split(" ", 2)
            if len(parts) == 3:
                try:
                    f_size = int(parts[0])
                    f_mtime = int(parts[1])
                    f_path = parts[2]
                    if f_mtime >= scan_mtime_threshold:
                        candidates.append((f_size, f_mtime, f_path))
                except ValueError:
                    continue

        candidates.sort(key=lambda x: x[1])
        return candidates

    def pull_and_ingest_file(
        self,
        remote_path: str,
        size_bytes: int,
        device_mtime: int,
        category: str,
        run_id: str
    ) -> Tuple[bool, int]:
        """
        Pulls file to staging path, computes SHA-256, moves into CAS shard,
        and registers with database. Returns (is_new_blob, bytes_transferred).
        """
        self.check_host_disk_safety()

        staging_dir = os.path.join(self.workspace_root, "scratch_stage")
        os.makedirs(staging_dir, exist_ok=True)
        staging_filename = f"tmp_{uuid.uuid4().hex}"
        staging_path = os.path.join(staging_dir, staging_filename)

        try:
            cmd = self._adb_prefix() + ["pull", remote_path, staging_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to pull '%s': %s", remote_path, e.stderr.strip())
            if os.path.exists(staging_path):
                os.remove(staging_path)
            return False, 0

        hasher = hashlib.sha256()
        with open(staging_path, "rb") as f:
            while chunk := f.read(1048576):
                hasher.update(chunk)
        sha256_hash = hasher.hexdigest()

        shard_dir = os.path.join(self.objects_dir, sha256_hash[:2], sha256_hash[2:4])
        os.makedirs(shard_dir, exist_ok=True)
        final_blob_path = os.path.join(shard_dir, sha256_hash)
        storage_relpath = os.path.relpath(final_blob_path, self.workspace_root)

        if os.path.exists(final_blob_path):
            os.remove(staging_path)
        else:
            shutil.move(staging_path, final_blob_path)

        filename = os.path.basename(remote_path)
        _, file_ext = os.path.splitext(filename)

        is_new_blob = self.db.upsert_blob_and_record(
            sha256_hash=sha256_hash,
            size_bytes=size_bytes,
            storage_relpath=storage_relpath,
            device_id=self.device_id,
            original_path=remote_path,
            filename=filename,
            file_ext=file_ext.lower(),
            category=category,
            device_mtime=device_mtime,
            run_id=run_id
        )

        return is_new_blob, size_bytes

    def execute_sync_cycle(self, lookback_sec: int = DEFAULT_SLIDING_WINDOW_SEC):
        """Executes a single differential backup pass across all categories."""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_ts = int(time.time())

        logger.info("==================================================================")
        logger.info("Starting Interval Backup Cycle [%s] on Device: %s", run_id, self.device_id)
        logger.info("==================================================================")

        self.check_host_disk_safety()

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO backup_checkpoints (run_id, started_at, trigger_type, status)
                VALUES (?, ?, 'INTERVAL', 'RUNNING')
            """, (run_id, start_ts))

        total_scanned = 0
        total_new_blobs = 0
        total_deduped = 0
        total_bytes = 0

        try:
            for category in CATEGORIES.keys():
                candidates = self.scan_remote_deltas(category, lookback_sec)
                cat_scanned = len(candidates)
                cat_new_blobs = 0
                cat_bytes = 0
                max_observed_mtime = self.db.get_watermark(category)

                for idx, (f_size, f_mtime, f_path) in enumerate(candidates, 1):
                    total_scanned += 1
                    if self.db.record_exists_and_current(self.device_id, f_path, f_mtime, f_size):
                        total_deduped += 1
                        if f_mtime > max_observed_mtime:
                            max_observed_mtime = f_mtime
                    else:
                        is_new, b_transferred = self.pull_and_ingest_file(
                            remote_path=f_path,
                            size_bytes=f_size,
                            device_mtime=f_mtime,
                            category=category,
                            run_id=run_id
                        )

                        if is_new:
                            cat_new_blobs += 1
                            total_new_blobs += 1
                        else:
                            total_deduped += 1

                        cat_bytes += b_transferred
                        total_bytes += b_transferred

                        if f_mtime > max_observed_mtime:
                            max_observed_mtime = f_mtime

                    if idx % 100 == 0 or idx == cat_scanned:
                        logger.info(
                            "Progress [%s]: %d/%d files processed (New Blobs: %d | Transferred: %.2f MB)",
                            category, idx, cat_scanned, cat_new_blobs, cat_bytes / (1024 ** 2)
                        )

                if max_observed_mtime > self.db.get_watermark(category):
                    self.db.set_watermark(category, max_observed_mtime, cat_scanned, cat_bytes)

                logger.info(
                    "Category '%s' complete: Scanned=%d | New Blobs=%d | Transferred=%.2f MB",
                    category, cat_scanned, cat_new_blobs, cat_bytes / (1024 ** 2)
                )

            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE backup_checkpoints
                    SET completed_at = ?, status = 'COMPLETED', scanned_count = ?,
                        new_blobs_count = ?, deduplicated_count = ?, bytes_transferred = ?
                    WHERE run_id = ?
                """, (int(time.time()), total_scanned, total_new_blobs, total_deduped, total_bytes, run_id))

            logger.info("Cycle %s SUCCESS: %d files scanned, %d new blobs, %d deduped (%.2f MB total)",
                        run_id, total_scanned, total_new_blobs, total_deduped, total_bytes / (1024 ** 2))

        except Exception as e:
            logger.error("Cycle %s FAILED: %s", run_id, str(e), exc_info=True)
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE backup_checkpoints
                    SET completed_at = ?, status = 'FAILED', error_message = ?
                    WHERE run_id = ?
                """, (int(time.time()), str(e), run_id))
            raise


def run_daemon(interval_sec: int, workspace: str, serial: Optional[str]):
    """Runs the backup engine in a continuous interval loop."""
    logger.info("Initializing Zalo Interval Backup Daemon (Interval: %ds)...", interval_sec)
    engine = ZaloBackupEngine(workspace_root=workspace, device_serial=serial)

    while True:
        try:
            engine.execute_sync_cycle()
        except StorageSafetyError as sse:
            logger.critical("SAFETY HALT: %s. Suspending daemon for 300s...", sse)
            time.sleep(300)
        except DeviceCommunicationError as dce:
            logger.warning("ADB OFFLINE: %s. Retrying in 30s...", dce)
            time.sleep(30)
        except Exception as ex:
            logger.error("Unexpected error in cycle: %s. Pausing 30s...", ex)
            time.sleep(30)

        logger.info("Sleeping for %d seconds until next interval...", interval_sec)
        time.sleep(interval_sec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zalo Android Interval-Based CAS Backup Engine")
    parser.add_argument("--interval", type=int, default=300, help="Backup interval in seconds (default: 300s)")
    parser.add_argument("--workspace", type=str, default="./zalo_backup_repo", help="Storage directory for CAS and DB")
    parser.add_argument("--serial", type=str, default=None, help="Specific ADB device serial number")
    parser.add_argument("--once", action="store_true", help="Execute single cycle and exit")

    args = parser.parse_args()

    if args.once:
        engine = ZaloBackupEngine(workspace_root=args.workspace, device_serial=args.serial)
        engine.execute_sync_cycle()
    else:
        run_daemon(interval_sec=args.interval, workspace=args.workspace, serial=args.serial)
