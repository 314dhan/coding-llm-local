import os
import uuid
from flask import Flask, render_template, request, jsonify, session
import ollama
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is not set. Add it to your .env file.")

conversation_histories: dict[str, list] = {}

SYSTEM_PROMPT = (
    "You are an expert coding assistant. Help the user with any programming question "
    "— explain code, debug issues, write code snippets. Be concise and clear. "
    "Use code blocks for all code."
)

MODEL = "qwen2.5-coder:7b"
MAX_HISTORY = 20


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    history = conversation_histories[session_id]
    history.append({"role": "user", "content": user_message})

    if len(history) > MAX_HISTORY:
        conversation_histories[session_id] = history[-MAX_HISTORY:]
        history = conversation_histories[session_id]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)

    try:
        response = ollama.chat(model=MODEL, messages=messages)
    except Exception as e:
        history.pop()
        return jsonify({"error": f"Model error: {e}"}), 502

    reply = response.message.content
    history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
