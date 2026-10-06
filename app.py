from flask import Flask, jsonify, render_template, request, session
from chatbot import SmartAssist
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

bot = SmartAssist()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()

    if not message:
        return jsonify({
            "ok": False,
            "error": "Please enter a message before sending."
        }), 400

    history = session.get("conversation_history", [])
    state = session.get("context", {})

    result = bot.reply(message=message, history=history, context=state)

    if result["ok"]:
        session["conversation_history"] = result["history"]
        session["context"] = result["context"]
        session.modified = True

    return jsonify(result), (200 if result["ok"] else 502)


@app.post("/clear-chat")
def clear_chat():
    session.pop("conversation_history", None)
    session.pop("context", None)
    return jsonify({"ok": True})


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "SmartAssist AI",
        "model": Config.GROQ_MODEL
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.FLASK_DEBUG)
