import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Config IA
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat')
def chat():
    # C'est cette ligne que ton site appelle quand tu cliques sur "Exécuter"
    msg = request.args.get('msg')
    if not msg:
        return jsonify({"response": "Signal vide."})
    try:
        response = model.generate_content(msg)
        return jsonify({"response": response.text})
    except Exception as e:
        # Si ça ne marche pas, NÉO va nous écrire l'erreur précise
        return jsonify({"response": f"Erreur système : {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

