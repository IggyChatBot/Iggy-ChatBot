"""
db_manager.py – Database Management
Component 4: Database Management

Handles:
- SQLite connection (local dev) — swap for Cloud SQL / Firebase in production
- Storing and retrieving FAQs, courses, schedules
- Logging all user interactions for analytics
- Session management records
"""

import sqlite3
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Database file path ────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'icct_chatbot.db')


class DatabaseManager:
    """
    Manages all database operations for the ICCT Chatbot.

    Uses SQLite for local development.
    To switch to Cloud SQL (MySQL/PostgreSQL):
        - Replace sqlite3 with mysql-connector-python or psycopg2
        - Update connect() with your Cloud SQL credentials

    To switch to Firebase Firestore:
        - Use firebase_admin SDK
        - Replace SQL queries with Firestore collection reads/writes
    """

    def __init__(self):
        self._connected = False
        self._init_db()

    # ── Connection ─────────────────────────────────────────────────
    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row   # Returns rows as dicts
        return conn

    def is_connected(self):
        return self._connected

    # ── Initialization ─────────────────────────────────────────────
    def _init_db(self):
        """Create all tables and seed initial FAQ data if empty."""
        try:
            with self._get_conn() as conn:
                cur = conn.cursor()

                # FAQs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS faqs (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        category    TEXT    NOT NULL,
                        question    TEXT    NOT NULL,
                        answer      TEXT    NOT NULL,
                        created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                        updated_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Courses table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS courses (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        code        TEXT    NOT NULL UNIQUE,
                        name        TEXT    NOT NULL,
                        college     TEXT    NOT NULL,
                        units       INTEGER,
                        description TEXT
                    )
                """)

                # Interaction logs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS interaction_logs (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id  TEXT    NOT NULL,
                        user_message TEXT   NOT NULL,
                        bot_reply    TEXT   NOT NULL,
                        intent       TEXT,
                        entities     TEXT,
                        timestamp    TEXT   DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Feedback table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id  TEXT    NOT NULL,
                        message_id  TEXT,
                        rating      INTEGER NOT NULL,
                        comment     TEXT,
                        timestamp   TEXT    DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
                self._seed_data(cur, conn)
                self._connected = True
                logger.info("DatabaseManager: initialized successfully.")

        except Exception as e:
            logger.error(f"DatabaseManager: init failed — {e}")
            self._connected = False

    def _seed_data(self, cur, conn):
        """Insert default FAQ and course data if tables are empty."""

        # ── Seed FAQs ──
        cur.execute("SELECT COUNT(*) FROM faqs")
        if cur.fetchone()[0] == 0:
            faqs = [
                ("enrollment", "How do I enroll at ICCT Colleges?",
                 "Visit the campus, fill out the Student Information Sheet, submit your documents, and pay the enrollment fee at the Cashier's Office."),
                ("enrollment", "When is the enrollment period?",
                 "1st Semester: June–July | 2nd Semester: November–December | Summer: March–April."),
                ("requirements", "What documents do I need to enroll?",
                 "PSA Birth Certificate, Form 138 or TOR, Certificate of Good Moral Character, 2x2 ID photos, and a valid ID."),
                ("courses", "What courses does ICCT offer?",
                 "BSIT, BSCS, BSCpE, BSBA, BSA, BSN, BEEd, BSEd, and Senior High School strands (STEM, ABM, HUMSS, GAS)."),
                ("tuition", "How much is the tuition fee?",
                 "Tuition is approximately ₱300–₱500 per unit depending on the program. Visit the Cashier's Office for the exact fee schedule."),
                ("scholarship", "What scholarships are available?",
                 "UniFAST/TDP, CHED scholarships, DSWD assistance, and institutional scholarships (academic, athletic, leadership)."),
                ("policy", "What is the attendance policy?",
                 "Students may not exceed 20% absences per subject per semester. Exceeding the limit results in a failing grade."),
                ("contact", "How do I contact the registrar?",
                 "Visit the Registrar's Office on campus. Office hours: Monday–Friday 8AM–5PM, Saturday 8AM–12PM."),
            ]
            cur.executemany(
                "INSERT INTO faqs (category, question, answer) VALUES (?, ?, ?)", faqs
            )

        # ── Seed Courses ──
        cur.execute("SELECT COUNT(*) FROM courses")
        if cur.fetchone()[0] == 0:
            courses = [
                ("BSIT",  "BS Information Technology",      "College of Computer Studies",    161, "Covers networking, web dev, databases, and software engineering."),
                ("BSCS",  "BS Computer Science",            "College of Computer Studies",    165, "Focuses on algorithms, AI, and theoretical computing."),
                ("BSCpE", "BS Computer Engineering",        "College of Computer Studies",    175, "Combines electronics engineering and computer science."),
                ("BSBA",  "BS Business Administration",     "College of Business",            129, "Covers management, marketing, finance, and entrepreneurship."),
                ("BSA",   "BS Accountancy",                 "College of Business",            176, "Prepares students for the CPA board examination."),
                ("BSN",   "BS Nursing",                     "College of Nursing",             158, "Prepares students for the NLE nursing board examination."),
                ("BEEd",  "Bachelor of Elementary Education","College of Education",          126, "Prepares teachers for elementary school level."),
                ("BSEd",  "Bachelor of Secondary Education","College of Education",           130, "Prepares teachers for high school level."),
            ]
            cur.executemany(
                "INSERT INTO courses (code, name, college, units, description) VALUES (?, ?, ?, ?, ?)",
                courses
            )

        conn.commit()

    # ── FAQ Queries ────────────────────────────────────────────────
    def get_faqs(self, category: str = None) -> list:
        """Return all FAQs, optionally filtered by category."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            if category:
                cur.execute("SELECT * FROM faqs WHERE category = ? ORDER BY id", (category,))
            else:
                cur.execute("SELECT * FROM faqs ORDER BY category, id")
            return [dict(row) for row in cur.fetchall()]

    def search_faq(self, query: str) -> dict | None:
        """
        Search FAQs for a question matching the user's query.
        Returns the best matching FAQ row or None.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()
            # Simple LIKE search — extend with FTS5 for better full-text search
            cur.execute(
                "SELECT * FROM faqs WHERE question LIKE ? OR answer LIKE ? LIMIT 1",
                (f"%{query}%", f"%{query}%")
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # ── Course Queries ─────────────────────────────────────────────
    def get_courses(self, college: str = None) -> list:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if college:
                cur.execute("SELECT * FROM courses WHERE college LIKE ?", (f"%{college}%",))
            else:
                cur.execute("SELECT * FROM courses ORDER BY college, code")
            return [dict(row) for row in cur.fetchall()]

    def get_course_by_code(self, code: str) -> dict | None:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM courses WHERE code = ?", (code.upper(),))
            row = cur.fetchone()
            return dict(row) if row else None

    # ── Interaction Logging ────────────────────────────────────────
    def log_interaction(self, session_id: str, user_message: str,
                        bot_reply: str, intent: str = None, entities: str = None):
        """Save every chat exchange to the database for analytics."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """INSERT INTO interaction_logs
                       (session_id, user_message, bot_reply, intent, entities)
                       VALUES (?, ?, ?, ?, ?)""",
                    (session_id, user_message, bot_reply, intent, str(entities))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"DatabaseManager: log_interaction failed — {e}")

    # ── Feedback ───────────────────────────────────────────────────
    def save_feedback(self, session_id: str, message_id: str,
                      rating: int, comment: str = "") -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO feedback (session_id, message_id, rating, comment) VALUES (?, ?, ?, ?)",
                    (session_id, message_id, rating, comment)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"DatabaseManager: save_feedback failed — {e}")
            return False

    # ── Analytics ──────────────────────────────────────────────────
    def get_interaction_stats(self) -> dict:
        """Return basic analytics from the interaction log."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM interaction_logs")
            total = cur.fetchone()[0]

            cur.execute("SELECT intent, COUNT(*) as count FROM interaction_logs GROUP BY intent ORDER BY count DESC")
            intents = [dict(row) for row in cur.fetchall()]

            cur.execute("SELECT COUNT(DISTINCT session_id) FROM interaction_logs")
            sessions = cur.fetchone()[0]

        return {"total_messages": total, "unique_sessions": sessions, "top_intents": intents}
