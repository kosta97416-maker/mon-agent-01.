import os
import json
import time
import random
import threading
from flask import Flask, render_template_string
import requests
from openai import OpenAI

app = Flask(__name__)

# --- MÉMOIRE DE FER (Persistence) ---
MEMOIRE_FILE = "neo_memory.json"

def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        with open(MEMOIRE_FILE, "r") as f:
            return json.load(f)
    return {"scans": 0, "butin": 0.0, "depenses": 0.0, "journal": []}

def sauvegarder_memoire(data):
    with open(MEMOIRE_FILE, "w") as f:
        json.dump(data, f)

# Initialisation des données
mission_data = charger_memoire()

# --- AGENT ÉCLAIREUR (Le Chasseur) ---
def agent_chasseur():
    global mission_data
    user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0"
    ]
    
    while True:
        # Simulation de scan discret
        time.sleep(random.randint(30, 90)) 
        mission_data["scans"] += 1
        
        # Logique de détection (Exemple: scan de Pastebin public)
        # Ici on simule une trouvaille légale de valeur abandonnée
        if random.random() > 0.95:
            gain = round(random.uniform(0.5, 10.0), 2)
            mission_data["butin"] += gain
            
            # Auto-paiement de NÉO (5% pour les frais de fonctionnement)
            frais = round(gain * 0.05, 2)
            mission_data["depenses"] += frais
            
            evenement = f"Détection : {gain} USDT récupérés. Frais de {frais} payés."
            mission_data["journal"].insert(0, f"{time.strftime('%H:%M:%S')} - {evenement}")
            sauvegarder_memoire(mission_data)

# --- INTERFACE DE COMMANDEMENT (Dashboard) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NÉO OS - Centre de Commande</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; }
        .header { border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 20px; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .card { border: 1px solid #00ff41; padding: 15px; background: rgba(0, 255, 65, 0.05); }
        .journal { height: 200px; overflow-y: scroll; border: 1px solid #333; padding: 10px; margin-top: 20px; font-size: 0.8em; }
        .glow { text-shadow: 0 0 5px #00ff41; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="glow">🛰️ NÉO : SYSTÈME D'EXTRACTION AUTONOME</h1>
            <p>Statut : <span style="color: yellow;">OPÉRATIONNEL (FURTIF)</span></p>
        </div>
        
        <div class="stats-grid">
            <div class="card">
                <h3>🚀 AGENTS</h3>
                <p>Scans effectués : {{ data.scans }}</p>
                <p>Actifs : 1 (Éclaireur Alpha)</p>
            </div>
            <div class="card">
                <h3>💰 BUTIN (USDT)</h3>
                <h2 class="glow">{{ "%.2f"|format(data.butin) }}</h2>
            </div>
            <div class="card">
                <h3>⛽ LOGISTIQUE</h3>
                <p>Dépenses NÉO : {{ "%.2f"|format(data.depenses) }}</p>
                <p>Mode : Auto-paiement</p>
            </div>
        </div>

        <h3>📝 JOURNAL DE BORD (MÉMOIRE)</h3>
        <div class="journal">
            {% for log in data.journal %}
                <p>> {{ log }}</p>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, data=mission_data)

if __name__ == "__main__":
    # Lancement du processus de chasse en tâche de fond
    threading.Thread(target=agent_chasseur, daemon=True).start()
    
    # Port Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
