import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Config IA avec sécurité
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat')
def chat():
    msg = request.args.get('msg')
    if not msg:
        return jsonify({"response": "Je t'écoute, Commandant. Pose-moi une question."})
    
    try:
        # Appel direct à l'IA
        response = model.generate_content(msg)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"response": f"Erreur de connexion : {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

