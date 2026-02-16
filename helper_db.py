import sqlite3
from client_db import *
def store_result(event: dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO session_results (
            user_id,
            timestamp,
            risk_score,
            severity,
            flag,
            explanation
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        int(event["user_id"]),
        str(event["timestamp"]),
        int(event["risk_score"]),
        str(event["severity"]),
        int(event["flag"]),
        str(event["reason"])
    ))

    conn.commit()
    conn.close()