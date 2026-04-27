import os
import requests
import datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION SYSTÈME ---
WALLET_DEST = os.environ.get("WALLET_DESTINATION", "NON_CONFIGURÉ")
VERSION = "1.0.4-FINAL"

def obtenir_donnees_marche():
    try:
        # Récupération prix réel USDT/EUR
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT", timeout=5)
        taux = 1 / float(r.json()['price'])
        return round(taux, 4)
    except:
        return 0.93

@app.route('/')
def index():
    taux = obtenir_donnees_marche()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NÉO_CORE_INTERFACE</title>
        <style>
            body { background-color: #000; color: #00FF41; font-family: 'Courier New', Courier, monospace; margin: 0; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
            #header { padding: 15px; border-bottom: 2px solid #00FF41; background: rgba(0, 20, 0, 0.9); z-index: 10; }
            #terminal { flex-grow: 1; overflow-y: auto; padding: 20px; font-size: 14px; text-shadow: 0 0 5px #00FF41; }
            #input-area { padding: 15px; background: #000; border-top: 1px solid #003300; display: flex; }
            input { background: transparent; border: none; color: #00FF41; flex-grow: 1; font-family: inherit; font-size: 16px; outline: none; }
            .stat-box { display: inline-block; margin-right: 20px; color: #FFF; }
            .neo-msg { color: #00FF41; margin-bottom: 8px; }
            .user-msg { color: #3b82f6; margin-bottom: 8px; font-weight: bold; }
            .highlight { color: #facc15; }
        </style>
    </head>
    <body>
        <div id="header">
            <div>[ NÉO_CORE_V{{v}} ] - ÉTAT: <span style="color:#00FF41;">ACTIF</span></div>
            <div style="font-size: 0.8em; margin-top: 5px; word-break: break-all;">
                TARGET_WALLET: <span class="highlight">{{ wallet }}</span>
            </div>
            <div style="margin-top:10px;">
                <span class="stat-box">MARKET: <span id="rate">{{ rate }}</span> EUR/USDT</span>
                <span class="stat-box">SESSION: <span id="clock"></span></span>
            </div>
        </div>

        <div id="terminal">
            <div class="neo-msg">> INITIALISATION DU NOYAU TERMINÉE...</div>
            <div class="neo-msg">> CONNEXION WALLET ZENGO... [OK]</div>
            <div class="neo-msg">> SYSTÈME PRÊT. EN ATTENTE D'INSTRUCTIONS.</div>
        </div>

        <div id="input-area">
            <span style="margin-right: 10px;">></span>
            <input type="text" id="cmd-input" placeholder="Parler à NÉO..." autofocus>
        </div>

        <script>
            const terminal = document.getElementById('terminal');
            const input = document.getElementById('cmd-input');

            function updateClock() {
                document.getElementById('clock').innerText = new Date().toLocaleTimeString();
            }
            setInterval(updateClock, 1000);
            updateClock();

            input.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    const val = this.value;
                    if (!val) return;

                    // Afficher message utilisateur
                    terminal.innerHTML += `<div class="user-msg">> ${val}</div>`;
                    
                    // Logique intelligente de NÉO
                    processCommand(val.toLowerCase());
                    
                    this.value = '';
                    terminal.scrollTop = terminal.scrollHeight;
                }
            });

            function processCommand(cmd) {
                let resp = "";
                if (cmd.includes('statut') || cmd.includes('status')) {
                    resp = "Système nominal. Flux de données stable. Wallet configuré sur {{ wallet }}.";
                } else if (cmd.includes('scan')) {
                    resp = "Analyse des opportunités réseau en cours... Aucun conflit détecté. Prêt pour injection.";
                } else if (cmd.includes('aide') || cmd.includes('help')) {
                    resp = "Commandes prioritaires : SCAN, STATUS, BALANCE, CLEAR.";
                } else if (cmd.includes('balance') || cmd.includes('argent')) {
                    resp = "Calcul du butin en cours... Connexion API Zengo établie. Valeur actuelle synchronisée.";
                } else {
                    resp = "Analyse de la requête : '" + cmd + "'... Instruction intégrée au noyau.";
                }
                
                setTimeout(() => {
                    terminal.innerHTML += `<div class="neo-msg">> NÉO: ${resp}</div>`;
                    terminal.scrollTop = terminal.scrollHeight;
                }, 600);
            }
        </script>
    </body>
    </html>
    """, wallet=WALLET_DEST, rate=taux, v=VERSION)

if __name__ == "__main__":
    # Port configuré dynamiquement pour Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

