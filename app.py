import os
import sqlite3
import logging
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
from utils.chatbot_utils import load_faq_data, prepare_embeddings, get_response
from gtts import gTTS
import tempfile

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Config
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "chatbot.log")
DB_PATH = "chatbot.db"

# Logging setup (stdout for Render)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load FAQ data & embeddings
faq_data = load_faq_data()

# Optional: save/load index from disk
INDEX_FILE = "faq_index.bin"
if os.path.exists(INDEX_FILE):
    from utils.chatbot_utils import faiss
    faq_index = faiss.read_index(INDEX_FILE)
    faq_embeddings = None  # embeddings are stored in index
else:
    faq_index, faq_embeddings = prepare_embeddings(faq_data)
    # Save index for future use
    from utils.chatbot_utils import faiss
    faiss.write_index(faq_index, INDEX_FILE)
# ---------------- Database Setup ---------------- #
def init_db():
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()
            return
        except sqlite3.DatabaseError:
            os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            sender TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- Routes ---------------- #
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

# ---------------- Signup ---------------- #
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not username or not email or not password:
            return render_template("signup.html", error="All fields are required.")

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (username, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="Username or email already exists.")
        conn.close()
        return redirect(url_for("login"))

    return render_template("signup.html")

# ---------------- Login ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

# ---------------- Logout ---------------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- Chat ---------------- #
@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        response, confidence = get_response(user_input, faq_data, faq_index)

        # Save chat to DB
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO chats (user_id, message, sender) VALUES (?, ?, ?)",
                     (session["user_id"], user_input, "user"))
        conn.execute("INSERT INTO chats (user_id, message, sender) VALUES (?, ?, ?)",
                     (session["user_id"], response, "bot"))
        conn.commit()
        conn.close()

        logging.info(f"{session['username']} - User: {user_input}")
        logging.info(f"{session['username']} - Bot: {response} (confidence: {confidence:.2f})")

        return jsonify({"response": response})
    except Exception as e:
        logging.error(f"Error in /chat: {e}")
        return jsonify({"error": "Internal server error"}), 500

# ---------------- Chat History ---------------- #
@app.route("/chat_history")
def chat_history():
    if "user_id" not in session:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user_id = session["user_id"]
    rows = conn.execute("SELECT * FROM chats WHERE user_id=? ORDER BY timestamp", (user_id,)).fetchall()
    conn.close()

    history = [{"sender": r["sender"], "message": r["message"], "timestamp": r["timestamp"]} for r in rows]
    return jsonify(history)

#-------------------history clearing------------------#
@app.route("/clear_history", methods=["POST"])
def clear_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chats WHERE user_id=?", (user_id,))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error clearing history for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- TTS ---------------- #
@app.route("/speak", methods=["GET"])
def speak():
    text = request.args.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    tts = gTTS(text=text, lang="en")
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp_file.name)
    return send_file(tmp_file.name, mimetype="audio/mpeg")

# ---------------- Health Check ---------------- #
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# ---------------- Main ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=DEBUG)
