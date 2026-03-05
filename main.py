# main.py
from __future__ import annotations

import sqlite3
from typing import Literal, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database.db import DB_PATH, init_db

app = FastAPI(title="Adaptive Gamified Quiz System (V0.1)")


# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def startup() -> None:
    init_db()


# -----------------------------
# DB helper
# -----------------------------
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Root
# -----------------------------
@app.get("/")
def root():
    return {"message": "Adaptive Gamified Quiz System running"}


# -----------------------------
# Models
# -----------------------------
class StartQuizIn(BaseModel):
    nickname: str


class AnswerIn(BaseModel):
    question_id: int
    chosen_option: Literal["A", "B", "C", "D"]


# -----------------------------
# Utility / Adaptivity (V0.1)
# -----------------------------
def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def compute_adaptation(is_correct: bool, response_time_ms: int, current_difficulty: int) -> Tuple[int, str]:
    """
    V0.1 rule-based adaptivity (demo-ready, simple):
    - Correct + fast => increase difficulty, "challenging" feedback
    - Incorrect OR slow => decrease difficulty, "supportive" feedback
    - Otherwise => keep difficulty, "neutral" feedback
    """
    fast = response_time_ms <= 5000   # <= 5 seconds
    slow = response_time_ms >= 12000  # >= 12 seconds

    if is_correct and fast:
        return clamp(current_difficulty + 1, 1, 3), "challenging"
    if (not is_correct) or slow:
        return clamp(current_difficulty - 1, 1, 3), "supportive"
    return current_difficulty, "neutral"


# -----------------------------
# API: Start quiz (create attempt)
# -----------------------------
@app.post("/quiz/start")
def start_quiz(payload: StartQuizIn):
    nickname = payload.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname cannot be empty")

    conn = db_conn()
    cur = conn.cursor()

    # Upsert user
    cur.execute("INSERT OR IGNORE INTO users (nickname) VALUES (?)", (nickname,))
    cur.execute("SELECT id FROM users WHERE nickname = ?", (nickname,))
    user_row = cur.fetchone()
    if user_row is None:
        conn.close()
        raise HTTPException(status_code=500, detail="Failed to create/load user")
    user_id = user_row["id"]

    # Create attempt
    cur.execute(
        """
        INSERT INTO attempts (user_id, started_at, total_score, correct_count, total_questions)
        VALUES (?, datetime('now'), 0, 0, 0)
        """,
        (user_id,),
    )
    attempt_id = cur.lastrowid

    conn.commit()
    conn.close()

    return {"attempt_id": attempt_id, "nickname": nickname}


# -----------------------------
# API: Next question (logs shown_at + shown_order)
# -----------------------------
@app.get("/quiz/{attempt_id}/next")
def next_question(attempt_id: int):
    conn = db_conn()
    cur = conn.cursor()

    # Validate attempt
    cur.execute("SELECT id FROM attempts WHERE id = ?", (attempt_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Pick a random question not yet served in this attempt
    cur.execute(
        """
        SELECT q.*
        FROM questions q
        WHERE q.id NOT IN (
          SELECT question_id FROM attempt_answers WHERE attempt_id = ?
        )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (attempt_id,),
    )
    q = cur.fetchone()
    if q is None:
        conn.close()
        return {"done": True, "message": "No more questions"}

    # shown_order = max(shown_order)+1 for this attempt
    cur.execute("SELECT COALESCE(MAX(shown_order), 0) AS m FROM attempt_answers WHERE attempt_id = ?", (attempt_id,))
    shown_order = int(cur.fetchone()["m"]) + 1

    # Log that question was shown (so we can compute response time later)
    cur.execute(
        """
        INSERT INTO attempt_answers (attempt_id, question_id, shown_order, shown_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (attempt_id, q["id"], shown_order),
    )
    conn.commit()
    conn.close()

    return {
        "done": False,
        "question": {
            "id": q["id"],
            "difficulty": q["difficulty"],
            "text": q["question_text"],
            "options": {
                "A": q["option_a"],
                "B": q["option_b"],
                "C": q["option_c"],
                "D": q["option_d"],
            },
        },
    }


# -----------------------------
# API: Answer question (instant feedback + scoring + response time + adaptivity)
# -----------------------------
@app.post("/quiz/{attempt_id}/answer")
def answer_question(attempt_id: int, payload: AnswerIn):
    conn = db_conn()
    cur = conn.cursor()

    # Validate attempt
    cur.execute("SELECT id FROM attempts WHERE id = ?", (attempt_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Load question
    cur.execute(
        "SELECT id, correct_option, difficulty FROM questions WHERE id = ?",
        (payload.question_id,),
    )
    q = cur.fetchone()
    if q is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found")

    correct_option = q["correct_option"]
    difficulty = int(q["difficulty"])

    is_correct = payload.chosen_option == correct_option
    points = 10 if is_correct else 0

    # Find the unanswered log row created by /next
    cur.execute(
        """
        SELECT id
        FROM attempt_answers
        WHERE attempt_id = ? AND question_id = ? AND answered_at IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (attempt_id, payload.question_id),
    )
    aa = cur.fetchone()
    if aa is None:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Question not served for this attempt (or already answered). Call /next first.",
        )

    attempt_answer_id = aa["id"]

    # Update row with answer, compute response time in ms via julianday diff
    cur.execute(
        """
        UPDATE attempt_answers
        SET
          answered_at = datetime('now'),
          chosen_option = ?,
          is_correct = ?,
          points_awarded = ?,
          response_time_ms = CAST((julianday(datetime('now')) - julianday(shown_at)) * 86400000 AS INTEGER)
        WHERE id = ?
        """,
        (payload.chosen_option, 1 if is_correct else 0, points, attempt_answer_id),
    )

    # Read response_time_ms
    cur.execute("SELECT response_time_ms FROM attempt_answers WHERE id = ?", (attempt_answer_id,))
    response_time_ms = int(cur.fetchone()["response_time_ms"] or 0)

    # Adaptive decision
    next_diff, feedback_style = compute_adaptation(is_correct, response_time_ms, difficulty)

    # Optional: store adaptivity decision (if columns exist)
    try:
        cur.execute(
            """
            UPDATE attempt_answers
            SET next_difficulty = ?, next_feedback_style = ?
            WHERE id = ?
            """,
            (next_diff, feedback_style, attempt_answer_id),
        )
    except sqlite3.OperationalError:
        # Columns not present; ignore for V0.1
        pass

    # Update attempt totals
    cur.execute(
        """
        UPDATE attempts
        SET
          total_score = total_score + ?,
          correct_count = correct_count + ?,
          total_questions = total_questions + 1
        WHERE id = ?
        """,
        (points, 1 if is_correct else 0, attempt_id),
    )

    conn.commit()
    conn.close()

    return {
        "question_id": payload.question_id,
        "chosen_option": payload.chosen_option,
        "correct": is_correct,
        "correct_option": correct_option,
        "points_awarded": points,
        "response_time_ms": response_time_ms,
        "adaptation": {
            "next_difficulty": next_diff,
            "feedback_style": feedback_style,
        },
    }


# -----------------------------
# Admin: quick logs for presentation screenshots
# -----------------------------
@app.get("/admin/attempts")
def list_attempts():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.id, u.nickname, a.started_at, a.total_questions, a.correct_count, a.total_score
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        ORDER BY a.id DESC
        LIMIT 50
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@app.get("/admin/attempt/{attempt_id}/answers")
def list_attempt_answers(attempt_id: int):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          aa.id,
          aa.attempt_id,
          aa.question_id,
          aa.shown_order,
          aa.shown_at,
          aa.answered_at,
          aa.chosen_option,
          aa.is_correct,
          aa.response_time_ms,
          aa.points_awarded
        FROM attempt_answers aa
        WHERE aa.attempt_id = ?
        ORDER BY aa.shown_order ASC
        """,
        (attempt_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows