from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["GET"])  # ← /api/chat en GET
def chat():
    try:
        msg = request.args.get("msg")  # ← args et non json
        response = model.generate_content(msg)
        return jsonify({"response": response.text})  # ← "response" et non "reply"
    except Exception as e:
        return jsonify({"response": f"Erreur : {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
