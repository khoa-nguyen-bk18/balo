#!/usr/bin/env python3
"""
export_zalo_conversations.py
============================
Forensic Conversation & Thread Exporter for Zalo Database Archives.
Based on Reverse-Engineering Analysis (REA) of Zalo's native schemas:
  - Table 'threads': Thread metadata, participants, display names
  - Table 'chats' / 'ChatContent': Message bodies, sender IDs, timestamps, JSON attachments
  - Table 'contact_profile_5': Contacts and address book profiles
  - Table 'group_info_v6': Group membership and admin metadata

Exports conversation history into JSON, CSV, and Markdown thread archives.
"""

import os
import sys
import json
import csv
import sqlite3
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZaloConversationExporter")


class ZaloConversationExtractor:
    """Extracts, normalizes, and exports Zalo message threads from SQLite databases."""

    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        if not os.path.isfile(self.db_path):
            raise FileNotFoundError(f"Zalo database not found: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._detect_tables()

    def _detect_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}
        self.has_chats = "chats" in tables
        self.has_chat_content = "ChatContent" in tables or "chat_content" in tables
        self.has_threads = "threads" in tables
        self.has_contacts = "contact_profile_5" in tables
        self.has_groups = "group_info_v6" in tables

        logger.info(
            "Detected tables: threads=%s, chats=%s, ChatContent=%s, contacts=%s, groups=%s",
            self.has_threads, self.has_chats, self.has_chat_content, self.has_contacts, self.has_groups
        )

    def get_contacts(self) -> Dict[str, Dict[str, Any]]:
        contacts = {}
        if not self.has_contacts:
            return contacts
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT uid, dpn AS display_name, phone, usr AS username, avt AS avatar_url, timestamp
            FROM contact_profile_5
        """)
        for r in cursor.fetchall():
            contacts[str(r["uid"])] = {
                "display_name": r["display_name"] or "",
                "phone": r["phone"] or "",
                "username": r["username"] or "",
                "avatar_url": r["avatar_url"] or "",
                "last_active": r["timestamp"]
            }
        return contacts

    def get_groups(self) -> Dict[str, Dict[str, Any]]:
        groups = {}
        if not self.has_groups:
            return groups
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id AS group_id, name AS group_name, creatorId, totalMem, admin_uids, member_uids, insertTs
            FROM group_info_v6
        """)
        for r in cursor.fetchall():
            groups[str(r["group_id"])] = {
                "group_name": r["group_name"] or "Unnamed Group",
                "creator_id": str(r["creatorId"]),
                "total_members": r["totalMem"],
                "admins": (r["admin_uids"] or "").split(","),
                "members": (r["member_uids"] or "").split(","),
                "joined_time": r["insertTs"]
            }
        return groups

    def get_threads(self) -> List[Dict[str, Any]]:
        threads = []
        if self.has_threads:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT userId, ownerId, ownerType, ts, fromId, displayName, msg, attach
                FROM threads
                ORDER BY ts DESC
            """)
            for r in cursor.fetchall():
                threads.append({
                    "user_id": str(r["userId"]),
                    "owner_id": str(r["ownerId"]),
                    "owner_type": "group" if r["ownerType"] == 1 else "direct",
                    "timestamp": r["ts"],
                    "from_id": str(r["fromId"]),
                    "display_name": r["displayName"] or "",
                    "last_message": r["msg"] or "",
                    "attach_raw": r["attach"] or ""
                })
        return threads

    def get_messages(self, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        messages = []
        cursor = self.conn.cursor()

        if self.has_chats:
            query = """
                SELECT ownerId, ownerType, fromId, fromName, cliMsgId, globalMsgId, ts, type, msg, attach
                FROM chats
            """
            params = []
            if owner_id:
                query += " WHERE ownerId = ? OR ownerId = ?"
                clean_id = owner_id.replace("group_", "")
                params.extend([owner_id, clean_id])
            query += " ORDER BY ts ASC"

            cursor.execute(query, params)
            for r in cursor.fetchall():
                attach_data = None
                raw_attach = r["attach"]
                if raw_attach:
                    try:
                        attach_data = json.loads(raw_attach)
                    except Exception:
                        attach_data = {"raw": raw_attach}

                formatted_time = ""
                if r["ts"]:
                    try:
                        formatted_time = datetime.fromtimestamp(r["ts"] / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass

                messages.append({
                    "owner_id": str(r["ownerId"]),
                    "owner_type": "group" if r["ownerType"] == 1 else "direct",
                    "from_id": str(r["fromId"]),
                    "from_name": r["fromName"] or "",
                    "client_msg_id": str(r["cliMsgId"] or ""),
                    "global_msg_id": str(r["globalMsgId"] or ""),
                    "timestamp_ms": r["ts"],
                    "datetime": formatted_time,
                    "msg_type": str(r["type"] or "text"),
                    "message_text": r["msg"] or "",
                    "attachment": attach_data
                })

        elif self.has_chat_content:
            table_name = "ChatContent" if "ChatContent" in [x[0] for x in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else "chat_content"
            query = f"""
                SELECT SenderId, CliMsgId, GlbMsgId, MsgType, TimeStamp, MsgContent, LocalPath
                FROM {table_name}
                ORDER BY TimeStamp ASC
            """
            cursor.execute(query)
            for r in cursor.fetchall():
                ts = r["TimeStamp"]
                formatted_time = ""
                if ts:
                    try:
                        formatted_time = datetime.fromtimestamp(ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                messages.append({
                    "owner_id": "ChatContent",
                    "owner_type": "direct",
                    "from_id": str(r["SenderId"]),
                    "from_name": "",
                    "client_msg_id": str(r["CliMsgId"] or ""),
                    "global_msg_id": str(r["GlbMsgId"] or ""),
                    "timestamp_ms": ts,
                    "datetime": formatted_time,
                    "msg_type": str(r["MsgType"] or "text"),
                    "message_text": r["MsgContent"] or "",
                    "attachment": {"local_path": r["LocalPath"]} if r["LocalPath"] else None
                })

        return messages

    def export_all(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        contacts = self.get_contacts()
        groups = self.get_groups()
        threads = self.get_threads()
        messages = self.get_messages()

        logger.info("Found %d contacts, %d groups, %d threads, %d messages.",
                    len(contacts), len(groups), len(threads), len(messages))

        # 1. Export JSON Archive
        archive = {
            "exported_at": datetime.now().isoformat(),
            "source_db": self.db_path,
            "contacts": contacts,
            "groups": groups,
            "threads": threads,
            "messages": messages
        }
        json_path = os.path.join(output_dir, "conversations_archive.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
        logger.info("Exported JSON archive: %s", json_path)

        # 2. Export CSV Messages Table
        csv_path = os.path.join(output_dir, "messages.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "datetime", "timestamp_ms", "owner_id", "owner_type",
                "from_id", "from_name", "msg_type", "message_text", "attachment_summary"
            ])
            for m in messages:
                att_summary = ""
                if m["attachment"]:
                    att_summary = json.dumps(m["attachment"], ensure_ascii=False)
                writer.writerow([
                    m["datetime"], m["timestamp_ms"], m["owner_id"], m["owner_type"],
                    m["from_id"], m["from_name"], m["msg_type"], m["message_text"], att_summary
                ])
        logger.info("Exported CSV spreadsheet: %s", csv_path)

        # 3. Export Formatted Markdown Transcripts by Thread
        chats_dir = os.path.join(output_dir, "transcripts")
        os.makedirs(chats_dir, exist_ok=True)

        grouped_messages = {}
        for m in messages:
            grouped_messages.setdefault(m["owner_id"], []).append(m)

        for owner_id, msgs in grouped_messages.items():
            name = owner_id
            if owner_id in groups:
                name = f"Group_{groups[owner_id]['group_name']}"
            elif owner_id in contacts:
                name = f"Contact_{contacts[owner_id]['display_name']}"

            safe_name = "".join([c if c.isalnum() or c in "._- " else "_" for c in name])
            transcript_file = os.path.join(chats_dir, f"{safe_name}_{owner_id}.md")

            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(f"# Conversation: {name} (ID: {owner_id})\n\n")
                f.write(f"**Total Messages:** {len(msgs)}\n\n---\n\n")

                for m in msgs:
                    sender = m["from_name"] or m["from_id"]
                    dt = m["datetime"] or f"Epoch {m['timestamp_ms']}"
                    f.write(f"### **[{dt}] {sender}** (`{m['from_id']}`)\n")
                    if m["message_text"]:
                        f.write(f"{m['message_text']}\n\n")
                    if m["attachment"]:
                        f.write(f"> **Attachment:** `{json.dumps(m['attachment'], ensure_ascii=False)}`\n\n")
                    f.write("\n")

        logger.info("Exported %d thread transcripts to: %s", len(grouped_messages), chats_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Zalo Conversations & Messages from SQLite Database")
    parser.add_argument("db", help="Path to Zalo SQLite database (e.g., databases/zalo or PC backup DB)")
    parser.add_argument("--output", default="./zalo_conversations_export", help="Output directory for exports")
    args = parser.parse_args()

    extractor = ZaloConversationExtractor(args.db)
    extractor.export_all(args.output)
