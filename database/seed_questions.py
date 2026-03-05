import sqlite3

DB_PATH = "database/quiz.db"

QUESTIONS = [
    {
        "question_text": "What does HTTP stand for?",
        "a": "HyperText Transfer Protocol",
        "b": "High Transfer Text Protocol",
        "c": "Hyper Transfer Text Process",
        "d": "Hyper Tool Transfer Protocol",
        "correct": "A",
        "difficulty": 1,
    },
    {
        "question_text": "Which SQL clause is used to filter rows?",
        "a": "ORDER BY",
        "b": "WHERE",
        "c": "GROUP BY",
        "d": "JOIN",
        "correct": "B",
        "difficulty": 1,
    },
    {
        "question_text": "In Python, which data type is immutable?",
        "a": "list",
        "b": "dict",
        "c": "set",
        "d": "tuple",
        "correct": "D",
        "difficulty": 1,
    },
    {
        "question_text": "What does REST most commonly emphasize?",
        "a": "Stateful sessions",
        "b": "Resource-based URLs",
        "c": "Binary protocols",
        "d": "Only SOAP",
        "correct": "B",
        "difficulty": 2,
    },
    {
        "question_text": "Which status code means 'Not Found'?",
        "a": "200",
        "b": "301",
        "c": "404",
        "d": "500",
        "correct": "C",
        "difficulty": 1,
    },
    {
        "question_text": "What is the main purpose of a database index?",
        "a": "Encrypt data",
        "b": "Speed up lookups",
        "c": "Reduce table size",
        "d": "Replace primary keys",
        "correct": "B",
        "difficulty": 2,
    },
    {
        "question_text": "Which algorithm family is scikit-learn primarily for?",
        "a": "Classical ML",
        "b": "Only deep learning",
        "c": "Only computer graphics",
        "d": "Only NLP transformers",
        "correct": "A",
        "difficulty": 1,
    },
    {
        "question_text": "In Git, what does 'commit' do?",
        "a": "Uploads to GitHub",
        "b": "Saves a snapshot locally",
        "c": "Deletes changes",
        "d": "Creates a new repo",
        "correct": "B",
        "difficulty": 1,
    },
    {
        "question_text": "Which metric is best for measuring engagement in your system logs?",
        "a": "Screen brightness",
        "b": "Number of attempts",
        "c": "Battery level",
        "d": "Mouse DPI",
        "correct": "B",
        "difficulty": 2,
    },
    {
        "question_text": "If a student answers fast and correctly, the adaptive system should likely:",
        "a": "Decrease difficulty",
        "b": "Increase difficulty",
        "c": "Stop the quiz",
        "d": "Remove feedback",
        "correct": "B",
        "difficulty": 3,
    },
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insert only if table is empty
    cur.execute("SELECT COUNT(*) FROM questions;")
    if cur.fetchone()[0] > 0:
        print("Questions already seeded.")
        conn.close()
        return

    cur.executemany(
        """
        INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (q["question_text"], q["a"], q["b"], q["c"], q["d"], q["correct"], q["difficulty"])
            for q in QUESTIONS
        ],
    )

    conn.commit()
    conn.close()
    print("Seeded 10 questions.")

if __name__ == "__main__":
    main()