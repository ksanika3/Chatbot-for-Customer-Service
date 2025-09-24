import os
import logging
from flask import Flask, request, jsonify, render_template
from utils.chatbot_utils import load_faq_data, prepare_embeddings, get_response

app = Flask(__name__)

# Config
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", "chatbot.log")

# Logging setup (stdout for Render)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load FAQ data & FAISS index
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

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        response, confidence = get_response(user_input, faq_data, faq_index)

        logging.info(f"User: {user_input}")
        logging.info(f"Bot: {response} (confidence: {confidence:.2f})")

        return jsonify({"response": response})
    except Exception as e:
        logging.error(f"Error in /chat: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
