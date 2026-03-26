"""Lightweight long-term memory backed by SQLite."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_plain_text(text: str, limit: int | None = None) -> str:
    cleaned = text or ""
    cleaned = cleaned.replace("\r", "\n")
    cleaned = cleaned.replace("```", " ")
    cleaned = cleaned.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = cleaned.replace("#", "")
    cleaned = cleaned.replace("`", "")
    cleaned = cleaned.replace(">", "")
    cleaned = re.sub(r"^[\-\*\d\.\s]+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = cleaned.strip()
    if limit is not None:
        return cleaned[:limit]
    return cleaned


def _extract_topics(*texts: str, limit: int = 8) -> List[str]:
    topics: List[str] = []
    pattern = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{2,}|[\u4e00-\u9fff]{2,12}")

    for text in texts:
        for token in pattern.findall(_to_plain_text(text)):
            token = token.strip()
            if token and token not in topics:
                topics.append(token)
            if len(topics) >= limit:
                return topics
    return topics


class MemoryStore:
    def __init__(self) -> None:
        db_path = os.getenv("MEMORY_DB_PATH", "data/agent_memory.db")
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    final_answer TEXT NOT NULL,
                    critique TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_user_time ON memory_interactions(user_id, created_at DESC)"
            )

        self._initialized = True

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_profile(self, conn: sqlite3.Connection, user_id: str) -> Dict[str, Any]:
        row = conn.execute(
            "SELECT profile_json FROM user_memory WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return {
                "interaction_count": 0,
                "recent_topics": [],
                "recent_questions": [],
                "last_plan": "",
                "last_answer_summary": "",
            }
        return json.loads(row["profile_json"])

    def _save_profile(self, conn: sqlite3.Connection, user_id: str, profile: Dict[str, Any]) -> None:
        payload = json.dumps(profile, ensure_ascii=False)
        now = _utc_now()
        conn.execute(
            """
            INSERT INTO user_memory(user_id, profile_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (user_id, payload, now),
        )

    def record_interaction(
        self,
        *,
        user_id: str,
        thread_id: str,
        question: str,
        plan: str,
        final_answer: str,
        critique: str,
    ) -> None:
        self.initialize()
        clean_question = _to_plain_text(question)
        clean_plan = _to_plain_text(plan, limit=1000)
        clean_answer = _to_plain_text(final_answer, limit=2000)
        clean_critique = _to_plain_text(critique, limit=1000)

        with self._lock, self._connect() as conn:
            profile = self._load_profile(conn, user_id)
            recent_topics = profile.get("recent_topics", [])
            for topic in _extract_topics(clean_question, clean_plan, clean_answer):
                if topic not in recent_topics:
                    recent_topics.append(topic)

            recent_questions = profile.get("recent_questions", [])
            if clean_question:
                recent_questions.append(clean_question)

            updated_profile = {
                "interaction_count": int(profile.get("interaction_count", 0)) + 1,
                "recent_topics": recent_topics[-8:],
                "recent_questions": recent_questions[-5:],
                "last_plan": clean_plan,
                "last_answer_summary": clean_answer[:400],
            }

            conn.execute(
                """
                INSERT INTO memory_interactions(
                    user_id, thread_id, question, plan, final_answer, critique, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    thread_id,
                    clean_question,
                    clean_plan,
                    clean_answer,
                    clean_critique,
                    _utc_now(),
                ),
            )
            self._save_profile(conn, user_id, updated_profile)
            conn.commit()

    def get_user_memory(self, user_id: str, limit: int = 5) -> Dict[str, Any]:
        self.initialize()
        with self._connect() as conn:
            profile = self._load_profile(conn, user_id)
            rows = conn.execute(
                """
                SELECT thread_id, question, plan, final_answer, critique, created_at
                FROM memory_interactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return {
            "user_id": user_id,
            "profile": profile,
            "recent_interactions": [dict(row) for row in rows],
        }

    def get_memory_context(self, user_id: str) -> str:
        data = self.get_user_memory(user_id, limit=3)
        profile = data["profile"]
        if not profile.get("interaction_count"):
            return ""

        lines = [
            f"历史交互次数：{profile.get('interaction_count', 0)}",
            "最近主题：" + "、".join(profile.get("recent_topics", [])),
            "最近提问：" + "；".join(profile.get("recent_questions", [])),
        ]

        summary = profile.get("last_answer_summary", "").strip()
        if summary:
            lines.append("上次回答摘要：" + summary)

        return "\n".join(line for line in lines if line and not line.endswith("："))


memory_store = MemoryStore()
