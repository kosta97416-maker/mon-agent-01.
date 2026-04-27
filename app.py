import os
import time
import threading
import random
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- MÉMOIRE DE MISSION ---
data_mission = {
    "scans": 0,
    "butin": 0.0,
    "depenses": 0.0,
    "journal": ["SYSTEM_READY: NÉO v3.0.1", "COMM_LINK: ESTABLISHED", "WAITING_FOR_COMMAND..."]
}

# --- INTERFACE MATRIX AVEC SYSTÈME DE CHAT ---
MATRIX_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NÉO_MATRIX_OS</title>
    <style>
        body { background-color: #000; color: #00FF41; font-family: 'Courier New', monospace; margin: 0; padding: 20px; overflow: hidden; }
        .container { border: 1px solid #00FF41; height: 92vh; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 0 15px #00FF41; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }
        .stat-box { border: 1px solid #003300; padding: 10px; background: rgba(0, 50, 0, 0.1); }
        #journal { flex-grow: 1; overflow-y: auto; border: 1px solid #003300; padding: 10px; font-size: 0.9em; }
        .input-area { margin-top: 20px; display: flex; border-top: 1px solid #00FF41; padding-top: 10px; }
        input { background: transparent; border: none; color: #00FF41; font-family: inherit; width: 100%; outline: none; }
        .green-glow { text-shadow: 0 0 8px #00FF41; }
    </style>
</head>
<body>
    <div class="container">
        <div class="stats">
            <div class="stat-box">[SCANS]: <span id="scans" class="green-glow">{{ data.scans }}</span></div>
            <div class="stat-box">[USDT]: <span id="butin" class="green-glow">{{ "%.2f"|format(data.butin) }}</span></div>
            <div class="stat-box">[FEE]: <span id="depenses" style="color: #ff0000;">{{ "%.2f"|format(data.depenses) }}</span></div>
        </div>

        <div id="journal">
            {% for log in data.journal %}
            <div>> {{ log }}</div>
            {% endfor %}
        </div>

        <div class="input-area">
            <span style="margin-right: 10px;">NEO@CMD:~$</span>
            <input type="text" id="user-input" placeholder="Taper un message..." onkeypress="handleKeyPress(event)">
        </div>
    </div>

    <script>
        function handleKeyPress(e) {
            if (e.keyCode === 13) {
                const input = document.getElementById('user-input');
                const msg = input.value;
                if (!msg) return;

                // Afficher le message localement
                const journal = document.getElementById('journal');
                journal.innerHTML = "<div>> USER: " + msg + "</div>" + journal.innerHTML;
                
                // Envoyer au serveur
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                })
                .then(response => response.json())
                .then(data => {
                    journal.innerHTML = "<div>> NEO: " + data.response + "</div>" + journal.innerHTML;
                });

                input.value = '';
            }
        }
        // Rafraîchir la page toutes les 30s pour voir les nouveaux scans
        setTimeout(() => { location.reload(); }, 30000);
    </script>
</body>
</html>
"""

# --- LOGIQUE DE RÉPONSE DE NÉO ---
@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get("message", "").lower()
    
    # Réponses personnalisées
    if "statut" in user_msg or "status" in user_msg:
        res = "LOG: Système opérationnel. Agents en mode furtif. Aucun blocage détecté."
    elif "argent" in user_msg or "butin" in user_msg:
        res = f"FINANCE: Nous avons actuellement {data_mission['butin']} USDT en réserve."
    elif "qui es-tu" in user_msg:
        res = "IDENTITÉ: Je suis NÉO, ton agent d'extraction autonome. Je ne dors jamais."
    else:
        res = "ANALYSE_REÇUE... Commande enregistrée dans la mémoire centrale."

    data_mission["journal"].insert(0, f"USER: {user_msg}")
    data_mission["journal"].insert(0, f"NEO: {res}")
    return jsonify({"response": res})

# --- LOGIQUE DE CHASSE (AUTOMATIQUE) ---
def agent_chasseur():
    while True:
        time.sleep(random.randint(20, 60))
        data_mission["scans"] += 1
        if random.random() > 0.9:
            val = round(random.uniform(0.1, 2.0), 2)
            data_mission["butin"] += val
            data_mission["depenses"] += round(val * 0.05, 2)
            data_mission["journal"].insert(0, f"BLOCKCHAIN_HIT: +{val} USDT")

@app.route('/')
def index():
    return render_template_string(MATRIX_HTML, data=data_mission)

if __name__ == "__main__":
    threading.Thread(target=agent_chasseur, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

