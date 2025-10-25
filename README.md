# Customer Service Chatbot 🤖

A lightweight, production-ready **FAQ chatbot** built with **Flask**, **FAISS**, and **Sentence Transformers**, packaged in Docker with a modern web UI.

## ✨ Features

* 🔍 **Semantic search** over FAQs using `sentence-transformers` + FAISS
* 🎨 **Modern chat UI** with stickers, typing indicator, and timestamps
* 🖥 **Flask backend** with REST API (`/chat`, `/health`)
* 🐳 **Dockerized** for easy deployment (Gunicorn included)
* 📊 **Logging** for conversations and errors
* 📱 **Responsive design** for desktop & mobile
* 🛡️ Input sanitization (prevents HTML/JS injection)

---

## 🛠 Tech Stack

* **Backend**: Flask, Gunicorn
* **ML/NLP**: SentenceTransformers (`all-MiniLM-L6-v2`), FAISS
* **Frontend**: HTML, CSS (Glassmorphism style), jQuery
* **Containerization**: Docker, multi-stage builds
* **Data**: CSV-based FAQ storage

---

## 📂 Project Structure

```
.
├── app.py                 # Flask app entrypoint
├── utils/
│   └── chatbot_utils.py   # Embeddings + FAISS + response logic
├── templates/
│   └── index.html         # Frontend UI
├── static/
│   ├── style.css          # Chat UI styles
│   ├── chatbot_avatar.webp
│   ├── sticker.webp
│   └── background.jpg
├── data/
│   └── faq_data.csv       # FAQ dataset
├── requirements.txt
├── Dockerfile
├── .gitignore
└── README.md              # ← (this file)
```

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/yourusername/customer-service-chatbot.git
cd customer-service-chatbot
```

### 2️⃣ Install dependencies

Create a virtual environment and install requirements:

```bash
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate     # (Windows)

pip install -r requirements.txt
```

### 3️⃣ Run locally

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🐳 Docker Deployment

### Build image

```bash
docker build -t chatbot .
```

### Run container

```bash
docker run -p 5000:5000 chatbot
```

Now visit [http://localhost:5000](http://localhost:5000).

---

## 📡 API Endpoints

### `POST /chat`

Send a message to the chatbot:

```json
{
  "message": "How can I reset my password?"
}
```

Response:

```json
{
  "response": "You can reset your password by clicking on 'Forgot Password' on the login page."
}
```

### `GET /health`

Health check (includes FAISS index info):

```json
{
  "status": "ok",
  "faq_loaded": true,
  "faiss_index_size": 42
}
```

---

## 📖 FAQ Data

All FAQs are stored in `data/faq_data.csv`.
It must have **two columns**:

```csv
question,answer
"What are your business hours?","We are open from 9 AM to 5 PM, Monday to Friday."
"How can I reset my password?","Click 'Forgot Password' on the login page."
```

To update the bot, just edit the CSV and restart the server.

---

## 🔮 Future Enhancements

* Conversation memory
* Admin panel for FAQ management
* Analytics dashboard (track top queries)
* Multilingual support
* Optional fallback to GPT models

---

## 👩‍💻 Author

Made with ❤️ by **Sagarika**.
GitHub: [Sagarika311](https://github.com/Sagarika311)

