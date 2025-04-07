import sqlite3

conn = sqlite3.connect("bank_data_demo.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, access_token TEXT, refresh_token TEXT)''')

def save_tokens(user_id: str, tokens: dict):
    c.execute("REPLACE INTO users VALUES (?, ?, ?)", (user_id, tokens["access_token"], tokens["refresh_token"]))
    conn.commit()

def get_user_tokens(user_id: str):
    c.execute("SELECT access_token, refresh_token FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    return {"access_token": row[0], "refresh_token": row[1]} if row else None
