PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  correct_option TEXT NOT NULL,
  difficulty INTEGER DEFAULT 1
);

CREATE TABLE attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  started_at TEXT,
  ended_at TEXT,
  total_score INTEGER,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE attempt_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id INTEGER,
  question_id INTEGER,
  chosen_option TEXT,
  is_correct INTEGER,
  response_time_ms INTEGER,
  FOREIGN KEY(attempt_id) REFERENCES attempts(id),
  FOREIGN KEY(question_id) REFERENCES questions(id)
);