import sqlite3

DB_PATH = "chatbot.db"

def fetch_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    cur = conn.cursor()

    # Fetch all users
    cur.execute("SELECT id, username, email, password FROM users")
    users = cur.fetchall()

    print("=== USERS ===")
    for user in users:
        print(dict(user))

    conn.close()

def fetch_chats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch last 10 chats
    cur.execute("""
        SELECT c.id, u.username, c.message, c.sender, c.timestamp
        FROM chats c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.timestamp DESC
        LIMIT 10
    """)
    chats = cur.fetchall()

    print("\n=== LAST 10 CHATS ===")
    for chat in chats:
        print(dict(chat))

    conn.close()

if __name__ == "__main__":
    fetch_users()
    fetch_chats()
