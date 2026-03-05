PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  correct_option TEXT NOT NULL CHECK (correct_option IN ('A','B','C','D')),
  difficulty INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  total_score INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  total_questions INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attempt_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,

  shown_order INTEGER NOT NULL,
  shown_at TEXT NOT NULL DEFAULT (datetime('now')),

  answered_at TEXT,
  chosen_option TEXT CHECK (chosen_option IN ('A','B','C','D')),
  is_correct INTEGER,
  response_time_ms INTEGER,
  points_awarded INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
  FOREIGN KEY(question_id) REFERENCES questions(id)
);

CREATE INDEX IF NOT EXISTS idx_answers_attempt_order
ON attempt_answers(attempt_id, shown_order);