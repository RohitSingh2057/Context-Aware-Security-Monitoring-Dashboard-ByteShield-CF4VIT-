import sqlite3

DB_NAME = "client.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        risk_score INTEGER,
        severity TEXT,
        flag INTEGER,
        explanation TEXT
    )
    """)

    conn.commit()
    conn.close()

# initialize DB at startup
init_db()